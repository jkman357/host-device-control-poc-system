# Protocol Test Vectors

These vectors are normative for byte-level encoder and parser alignment.

Both implementation repositories shall:

1. encode every vector to the exact `frame_hex`;
2. decode every vector to the declared fields;
3. reject a frame after a controlled CRC corruption;
4. preserve the request sequence in direct responses;
5. record the tested Protocol file SHA-256 and implementation commit.

Passing these vectors proves byte-level agreement only. Hardware timing, buffering, loss, recovery, and long-duration behavior require separate evidence.
