## Roadmap for PeARS V1.0


> WIP. Feel free to add the features necessary for the release

## PeARS scope of the fist release:

1. We not have a semi-working DHT implementation. The current implementaion does not go well with the Flask app we have since the twisted I use is asynchronous communication and Flask itself is synchronous. This is to be replaced with a better implementation preferably in a different language that deals with concurrency and distribution a bit better. The language I propose for our DHT is Elixir and it has a minimal chord DHT implementation which can be used. Things to be implemented so as to integrate with PeARS are:
    * K-nearest node search.
    * Distributed locality sensitive hashing for better search results on the DHT.
    * Setup a stun server to do proper TCP/UDP packet relay.

