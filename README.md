# A Galileo HAS Parser: GHASP

The Galileo High Accuracy Service (HAS) was declared operational on 24th January 2023, during the annual European Space Conference. Through HAS, Galileo is broadcasting orbit, clock and measurement corrections enabling decimeter level positioning. 

HAS corrections are distributed through the E6B signal, which adopts a high-parity vertical Reed-Solomon encoding scheme. Thus, E6B signals need to be decoded in order to recover the HAS corrections enabling Precise Point Positioning (PPP).   

In order to foster the use of HAS corrections, a HAS parser has been developed. This is the user manual of such parser, which has been denoted as Galileo HAS Parser (GHASP).

GHASP supports several data types from different receiver types and converts E6B data messages, recorded as binary streams, into actual PPP corrections. The outputs of the parser are four Comma-Separated Values (CSV) files containing the different correction types. The corrections can be easily loaded using any scientific programming language and used for different analyses in addition to PPP applications.
