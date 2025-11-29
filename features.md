# features
*how documentation is maintained*

All code is documented using *feature-modular specifications*, defined as follows:

A *feature* defines a unitary capability. Each feature is either a *root feature* `A`, in which case it lives in `/features/A/`; or a *sub-feature* `X` of some other feature `A/B/C` in which case it lives in `/features/A/B/C/X`.

Each feature has four files:

    spec.md : user-facing documentation of why the feature exists, what it does, and how to use it. Language should be simple and concise, max 150 words.

    pseudocode.md : natural-language step-by-step definitions of new functions, modifications to existing functions, and where changes should be made in the program

    code.md : same as pseudocode.md, but with the natural language pseudocode translated into actual code. Mixing languages and products is fine, eg. specifying interaction between client and server.

    test.md : instructions for testing the feature, including manual test steps and/or automated test commands. Should verify the feature works as specified.

The actual output code lives in the folder `products/`, with subfolders for each actual product (eg. client/server). Each product should have its own spec.md file for notes and documentation.

The rules are:

    - A/B/spec.md is maintained as the source of truth about the user/developer's intention
    - A/B/pseudocode.md is allowed to be a partial implementation of A/B/spec.md, but must reflect the actual code
    - spec.md and pseudocode.md should contain no references to any language, API or SDK - just natural language
    - A/B/code.md should reflect the actual code
    - each feature should contain only one feature specification. Additional detail should be added as a sub-feature, rather than extending spec.md
    - product code should always refer back to the specific feature path it implements (via comments)
    - ad-hoc changes to product code should be fed back to updated code, pseudocode and spec docs.