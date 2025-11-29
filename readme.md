# boomer
*simulating the sound of a big room*

Our starting point is two audio files:

    ref.wav : audio recorded from the output of a DJ mixer
    room.wav : the same audio, recorded by an audience member at Sonar Lisboa 2025

Our goal is to create a real-time audio processing filter system that can convert ref.wav into room.wav, to simulate the effect of a big sound system in a big room full of people. This would allow musicians and performers to better understand and control how their music is perceived by the audience.

## discussion

room.wav is the result of playing ref.wav through the following:

    - output from a large PA system
    - echo, resonance, reverb interactions with the venue
    - absorption by the audience
    - recording on a cellphone

Our aim is to simulate each of these elements as a set of individual audio filters / processors, and to chain them together.

## method

We have a range of possible processors (=filter, etc) we can use to simulate the effect of the room. For each processor, we need to be able to do two things:

    - measure some quality of a given audio file
    - compare the measurements of two audio files

Our process then will be:

    - measure q_ref and q_room (for ref.wav and room.wav)
    - apply processor with settings P to ref.wav to make test.wav
    - measure q_test and compare with q_room
    - iteratively adjust P until q_test is as close to q_room as we can make it

## system

We will start by creating a real-time filter and interactive playback interface, to ensure that whatever processors we develop can actually run in real time (although offline analysis is always allowed). Initially, there will be no filter; we will just measure our various q_ref / q_test / q_room properties and display them interactively. The goal is to gradually form an intuitive understanding of what works and what doesn't.
