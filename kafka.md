# Kafka and the Elastic Stack


> "Kafka is a distributed, partitioned, replicated commit log service. It provides the functionality of a messaging system, but with a unique design."


## Kafka

| Term           |                       Meaning                  |
|:-------------  |:---------------------------------------------- |
| topic          | feed of messages associated with same category |
| partition      | an ordered, immutable sequence of messages associated with a topic |
| broker         | a single Kafka server, part of the cluster                |
| producers      | processes that publish messages to a Kafka topic                |
| consumers      | processes that subscribe to topics and process the feed of published messages                |
| consumer group | name of group consumers subscribe to. each message published to a topic is delivered to one consumer instance within each of these groups.              |


### Running

let's assume we unpack and change into the release directory

```bash
$ tar -xzf kafka_2.11-0.9.0.0.tgz
$ cd kafka_2.11-0.9.0.0
```

Now we will find a few executable scripts in the `bin` directory.

To quickly bootstrap Zookeeper, Kafka comes packaged with it.

```
$ bin/zookeeper-server-start.sh config/zookeeper.properties
```

Once we have a zookeeper cluster running, we can start up our Kafka cluster

```
$ bin/kafka-server-start.sh config/server.properties
```

Now what? Currently, nothing is happening... but, it is important to look at `/tmp/kafka-logs`
Once we start loading in data, you will see all the topic log data there. Similar to how you find Elasticsearch indices in `{path.home}/data`

By default, topics are dynamically created as messages start flowing into them. The 
configuration parameter for this is:

```
auto.create.topics.enable=true
```

To explicitly create a topic with specific options, you can use the `kafka-topics.sh` script found in the `bin` directory

```
bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 3 --topic test
```

## Logstash

Since Logstash 1.5, we have bundled `logstash-input-kafka` and `logstash-output-kafka` into 
our bundled Logstash release artifact.

#### Release Version Matrix
| Logstash  | logstash-input-kafka  | logstash-output-kafka | Kafka Target |
|:----:|:-------:|:-----:|:------:|
| 1.5  | 1.0.1   | 1.0.0 |  0.7.x |
| 2.0  | 2.0.2   | 2.0.1 |  0.8.x |
| 2.1  | 2.0.4   | 2.0.2 |  0.8.x |
| 2.2  | 2.0.4   | 2.0.2 |  0.8.x |
| 2.3  | 2.0.4   | 2.0.2 |  0.8.x |
| 5.0  | 3.0.0   | 3.0.0 |  0.9.x? |

#### Codecs

Kafka has its own notion of codecs, it calls them "Encoders" and "Decoders". For this 
reason, it is both possible to leverage Logstash codecs as well as Kafka serializers to manage 
message serialization and deserialization into and out of Logstash Event Objects.

The default codec is `json`. Some other logstash codecs that are relevant to the Kafka 
ecosystem are `plain`, `avro`, and `avro_schema_registry`. These Avro codecs are not packaged with Logstash and must be installed using:

```
$ bin/plugin install logstash-codec-avro
```
```
$ bin/plugin install logstash-codec-avro_schema_registry
```

If users wish to re-use their existing Kafka encoders/decoders, they can specify them using

```
# input
decoder_class => 'kafka.serializer.DefaultDecoder'
# output
value_serializer => 'org.apache.kafka.common.serialization.StringSerializer'
```

Since these classes are not in Logstash's classpath, you must explicitly add the appropriate 
library into your java classpath.

```
export CLASSPATH=$CLASSPATH:/path/to/kafkaserializers.jar
```
### Input

```
input {
  kafka {
    zk_connect => "..."
    topic_id => "your_topic"
    group_id => "logstash"
    consumer_threads => 1
    queue_size => 20
    auto_offset_reset => largest
    reset_beginning => false
  }
}
```

Runtime Considerations

* Are you consuming from all partitions?
* If you are having trouble keeping up with Kafka, what is your partition-consumer_threads ratio?
* What is your consumer lag?

Runtime Considerations Specific to multiple Logstash Instances

* are you sure they are all a part of the same `group_id`?
* As you are adding or removing new logstash nodes, are you noticing Kafka rebalancing the partition assignments within your group evenly?

#### Maintaining State

* Underneath, Logstash uses Kafka's offset management to mark messages within a topic as "read".
* Since Kafka 0.8.2, these can either be stored in Kafka or Zookeeper (default: Zookeeper)
* `auto_commit_interval_ms => 1000`, Logstash commits these offsets to Zookeeper every second
* Potential loss of events upon failure restart
* These two parameters must be understood and potentially used: `auto_offset_reset`, `reset_beginning`

### Output

```
output {
  kafka {
    bootstrap_servers => "localhost:9092"
    topic_id => "your_topic"
    acks => "1"
  }
}
```

Runtime Considerations

* are you producing to all partitions evenly? do you care about message order?
* If you feel things are slow, and you do not care for message receival guarantees... set `acks => 0`


## Tools

Kafka comes with a wide variety of tools to monitor things like consumer lag.

* **JMX**

    logstash java variables
    ```
    export LS_JAVA_OPTS="
    -Dcom.sun.management.jmxremote.authenticate=false
    -Dcom.sun.management.jmxremote.port=3000
    -Dcom.sun.management.jmxremote.ssl=false"
    ```
    
    jmx input plugin
    ```
    input {
    	jmx {
    		path => '/path/to/jmx'
    		polling_frequency => 5
    	}
    }
    output {
    	elasticsearch {}
    }
    ```
    You will get data like `MessagesInPerSecond` for each topic, or `ConsumerLag`
    
    
* **ConsumerOffsetChecker**
   Kafka comes packaged with a little script to help fetch offset information. You can use this to check that Logstash is keeping up and the queue is not growing too large
	```
	$ bin/kafka-run-class.sh kafka.tools.ConsumerOffsetChecker --zkconnect localhost:2181 --group test
	Group           Topic                          Pid Offset          logSize         Lag             Owner
my-group        my-topic                       0   0               0               0               test_jkreps-mn-1394154511599-60744496-0
my-group        my-topic                       1   0               0               0               test_jkreps-mn-1394154521217-1a0be913-0

	```

### Known Issues / Concerns

- Consumer is not balanced. This seems to affect some installations of `0.8.2` clusters with `logstash-input-kafka`. New tests were added to verify this and fix it. 
- Decoding of messages in `logstash-input-kafka` is single-threaded (performance issue)
- Logstash gives up control of offset maintainance to Kafka. This does not always make it easy for users to re-read old data from specific offset (not oldest or newest).
- We can lose data (because of the internal queueing) since we have no acking in Logstash between Outputs and Inputs

# What's Next

## 3.0

Since Kafka development went full scale with the help of Confluent, new features are introduced into Kafka at record speeds. Backwards compatibility is always a question when dealing with protocol changes between versions.

Kafka 0.9.0.0 was recently released, These brokers are mostly backwards compatible with the client libraries (aka Logstash). Next version will break that. This means we need to up our support of these plugins as more and more customers span these different versions. The big feature that 0.9 introduces is SSL support, and much better consumer APIs. Another change is that the default offset storage has been moved to Kafka.

### Roadmap
- We plan on launching a complete rewrite of these plugins using newer consumer and producer APIs found in the Java libraries
- logstash-input-kafka 3.0.0.beta3 was released recently (SSL / 0.9)
- logstash-output-kafka 3.0.0.beta1 was released recently (SSL / 0.9)
- input and output plugins will sync up release versions
- Benchmarks. Specifically capacity planning with Kafka -> ES pipeline

	
