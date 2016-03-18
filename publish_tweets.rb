require 'avro'
require 'poseidon'

TWEPOCH = 1288834974657
SCHEMA = Avro::Schema.parse(File.read("twitter.avsc"))

def gen_random_events(length=100)
  time = TWEPOCH
  events = []
  length.times {
    events << {"username" => "name", "tweet" => "I have things to say!", "timestamp" => time}
    time += Random.new.rand(1..300)
  }
  events
end

def encode(event)
  dw = Avro::IO::DatumWriter.new(SCHEMA)
  buffer = StringIO.new
  encoder = Avro::IO::BinaryEncoder.new(buffer)
  dw.write(event, encoder)
  buffer.string
end

N = 1000
N_BATCH = 100
topic = "avro_meet_kafka"
producer = nil
while producer.nil?
  begin
    producer = Poseidon::Producer.new(["172.18.0.2:9092"], "my_test_producer")
    gen_random_events(N).each_slice(N_BATCH) { |batch|
      producer.send_messages(batch.map{|m| Poseidon::MessageToSend.new(topic, encode(m))})
    }
    break
  rescue Poseidon::Errors::UnableToFetchMetadata
    producer = nil
  end
end
