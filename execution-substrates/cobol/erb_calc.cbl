       *> ERB Calculation Module (GENERATED - DO NOT EDIT)
       *> Generated from: effortless-rulebook/effortless-rulebook.json
       *> GnuCOBOL free-format: cobc -free -m erb_calc.cbl
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ERBCALC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-FIND-NEEDLE   PIC X(500).
       01 WS-FIND-HAYSTACK PIC X(500).
       01 WS-FIND-RESULT   PIC X(5).
       01 WS-FIND-I       PIC 9(6).
       01 WS-FIND-LEN     PIC 9(6).
       01 WS-FIND-NLEN    PIC 9(6).
       01 WS-TEMP-1       PIC X(500).
       01 WS-TEMP-2       PIC X(500).
       01 WS-TEMP-3       PIC X(500).
       01 WS-TEMP-4       PIC X(500).
       01 WS-TEMP-5       PIC X(500).
       01 WS-TEMP-6       PIC X(500).
       01 WS-TEMP-7       PIC X(500).
       01 WS-TEMP-8       PIC X(500).
       01 WS-TEMP-9       PIC X(500).
       01 WS-TEMP-10      PIC X(500).
       LINKAGE SECTION.
       COPY "erb_copy".
       PROCEDURE DIVISION USING RECORD.
       MAIN-CALC.
           PERFORM COMPUTE-ALL-FIELDS
           GOBACK.
       .

       *> ========== LANGUAGECANDIDATES ==========
       *> Level 1
       CALC-HAS-GRAMMAR.
           IF RECORD-HAS-SYNTAX = "true"
              MOVE "true" TO RECORD-HAS-GRAMMAR
           ELSE
              MOVE "false" TO RECORD-HAS-GRAMMAR
           END-IF
       .

       CALC-QUESTION.
           STRING 'Is ' DELIMITED BY SIZE RECORD-NAME DELIMITED BY SIZE ' a language?' DELIMITED BY SIZE INTO RECORD-QUESTION
       .

       CALC-PREDICTED-BIOLOGICAL-LANGUAGE-CORE.
           IF (RECORD-BIO-IS-EVOLVED-COMMUNICATION-SYSTEM = 'true') AND (RECORD-BIO-HAS-SEMANTICITY = 'true') AND (RECORD-BIO-HAS-ARBITRARINESS = 'true') AND (RECORD-BIO-HAS-DISCRETENESS = 'true') AND (RECORD-BIO-HAS-DUALITY-OF-PATTERNING = 'true') AND (RECORD-BIO-HAS-PRODUCTIVITY = 'true') AND (RECORD-BIO-HAS-DISPLACEMENT = 'true') AND (RECORD-BIO-HAS-CULTURAL-TRANSMISSION = 'true')
              MOVE "true" TO RECORD-PREDICTED-BIOLOGICAL-LANGUAGE-CORE
           ELSE
              MOVE "false" TO RECORD-PREDICTED-BIOLOGICAL-LANGUAGE-CORE
           END-IF
       .

       CALC-BIO-HOCKETT-SCORE.
           MOVE 0 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-SEMANTICITY = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-ARBITRARINESS = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-DISCRETENESS = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-DUALITY-OF-PATTERNING = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-PRODUCTIVITY = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-DISPLACEMENT = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-CULTURAL-TRANSMISSION = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-INTERCHANGEABILITY = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-FEEDBACK = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-BROADCAST-TRANSMISSION = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
           IF RECORD-BIO-HAS-RAPID-FADING = 'true'
              MOVE 1 TO WS-TEMP-1
           ELSE
              MOVE 0 TO WS-TEMP-1
           END-IF
           ADD WS-TEMP-1 TO RECORD-BIO-HOCKETT-SCORE
       .

       CALC-IS-DESCRIPTION-OF.
           IF RECORD-DISTANCE-FROM-CONCEPT > 1
              MOVE "true" TO RECORD-IS-DESCRIPTION-OF
           ELSE
              MOVE "false" TO RECORD-IS-DESCRIPTION-OF
           END-IF
       .

       CALC-IS-OPEN-CLOSED-WORLD-CONFLICTED.
           IF (RECORD-IS-OPEN-WORLD = 'true') AND (RECORD-IS-CLOSED-WORLD = 'true')
              MOVE "true" TO RECORD-IS-OPEN-CLOSED-WORLD-CONFLICTED
           ELSE
              MOVE "false" TO RECORD-IS-OPEN-CLOSED-WORLD-CONFLICTED
           END-IF
       .

       CALC-RELATIONSHIP-TO-CONCEPT.
           IF RECORD-DISTANCE-FROM-CONCEPT = 1
              MOVE 'IsMirrorOf' TO RECORD-RELATIONSHIP-TO-CONCEPT
           ELSE
              MOVE 'IsDescriptionOf' TO RECORD-RELATIONSHIP-TO-CONCEPT
           END-IF
       .

       *> Level 2
       CALC-PREDICTED-ANSWER.
           IF ((RECORD-HAS-SYNTAX = 'true') AND (RECORD-IS-PARSED = 'true') AND (RECORD-IS-DESCRIPTION-OF = 'true') AND (RECORD-HAS-LINEAR-DECODING-PRESSURE = 'true') AND (RECORD-RESOLVES-TO-AN-AST = 'true') AND (RECORD-IS-STABLE-ONTOLOGY-REFERENCE = 'true') AND (NOT (RECORD-CAN-BE-HELD = 'true')) AND (NOT (RECORD-HAS-IDENTITY = 'true'))) OR (RECORD-BIO-HOCKETT-SCORE > 0)
              MOVE "true" TO RECORD-PREDICTED-ANSWER
           ELSE
              MOVE "false" TO RECORD-PREDICTED-ANSWER
           END-IF
       .

       CALC-PREDICTED-BIOLOGICAL-LANGUAGE-STRICT.
           IF (RECORD-PREDICTED-BIOLOGICAL-LANGUAGE-CORE = 'true') AND (RECORD-BIO-HAS-INTERCHANGEABILITY = 'true') AND (RECORD-BIO-HAS-FEEDBACK = 'true')
              MOVE "true" TO RECORD-PREDICTED-BIOLOGICAL-LANGUAGE-STRICT
           ELSE
              MOVE "false" TO RECORD-PREDICTED-BIOLOGICAL-LANGUAGE-STRICT
           END-IF
       .

       CALC-PREDICTION-PREDICATES.
           IF RECORD-HAS-SYNTAX = 'true'
              MOVE 'Has Syntax' TO WS-TEMP-1
           ELSE
              MOVE 'No Syntax' TO WS-TEMP-1
           END-IF
           IF RECORD-IS-PARSED = 'true'
              MOVE 'Requires Parsing' TO WS-TEMP-2
           ELSE
              MOVE 'No Parsing Neede' TO WS-TEMP-2
           END-IF
           IF RECORD-IS-DESCRIPTION-OF = 'true'
              MOVE 'Describes the thing' TO WS-TEMP-3
           ELSE
              MOVE 'Is the Thing' TO WS-TEMP-3
           END-IF
           IF RECORD-HAS-LINEAR-DECODING-PRESSURE = 'true'
              MOVE 'Has Linear Decoding Pressure' TO WS-TEMP-4
           ELSE
              MOVE 'No Decoding Pressure' TO WS-TEMP-4
           END-IF
           IF RECORD-RESOLVES-TO-AN-AST = 'true'
              MOVE 'Resolves to AST' TO WS-TEMP-5
           ELSE
              MOVE 'No AST' TO WS-TEMP-5
           END-IF
           IF RECORD-IS-STABLE-ONTOLOGY-REFERENCE = 'true'
              MOVE 'Is Stable Ontology' TO WS-TEMP-6
           ELSE
              MOVE 'Not ''Ontology''' TO WS-TEMP-6
           END-IF
           IF RECORD-CAN-BE-HELD = 'true'
              MOVE 'Can Be Held' TO WS-TEMP-7
           ELSE
              MOVE 'Can''t Be Held' TO WS-TEMP-7
           END-IF
           IF RECORD-HAS-IDENTITY = 'true'
              MOVE 'Has Identity' TO WS-TEMP-8
           ELSE
              MOVE 'Has no Identity' TO WS-TEMP-8
           END-IF
           STRING WS-TEMP-1 DELIMITED BY SIZE ' & ' DELIMITED BY SIZE WS-TEMP-2 DELIMITED BY SIZE ' & ' DELIMITED BY SIZE WS-TEMP-3 DELIMITED BY SIZE ' & ' DELIMITED BY SIZE WS-TEMP-4 DELIMITED BY SIZE ' & ' DELIMITED BY SIZE WS-TEMP-5 DELIMITED BY SIZE ', ' DELIMITED BY SIZE WS-TEMP-6 DELIMITED BY SIZE ' AND ' DELIMITED BY SIZE WS-TEMP-7 DELIMITED BY SIZE ', ' DELIMITED BY SIZE WS-TEMP-8 DELIMITED BY SIZE INTO RECORD-PREDICTION-PREDICATES
       .

       *> Level 3
       CALC-PREDICTION-FAIL.
           IF NOT (RECORD-PREDICTED-ANSWER = RECORD-IS-LANGUAGE)
              IF RECORD-PREDICTED-ANSWER = 'true'
                 MOVE 'Is' TO WS-TEMP-2
              ELSE
                 MOVE 'Isn''t' TO WS-TEMP-2
              END-IF
              IF RECORD-IS-LANGUAGE = 'true'
                 MOVE 'Is' TO WS-TEMP-3
              ELSE
                 MOVE 'Is Not' TO WS-TEMP-3
              END-IF
              STRING RECORD-NAME DELIMITED BY SIZE ' ' DELIMITED BY SIZE WS-TEMP-2 DELIMITED BY SIZE ' a Family Feud Language, but ' DELIMITED BY SIZE WS-TEMP-3 DELIMITED BY SIZE ' marked as a ''Language Candidate.''' DELIMITED BY SIZE INTO WS-TEMP-1
           ELSE
              MOVE '' TO WS-TEMP-1
           END-IF
           IF RECORD-IS-OPEN-CLOSED-WORLD-CONFLICTED = 'true'
              MOVE ' - Open World vs. Closed World Conflict.' TO WS-TEMP-4
           ELSE
              MOVE '' TO WS-TEMP-4
           END-IF
           STRING WS-TEMP-1 DELIMITED BY SIZE WS-TEMP-4 DELIMITED BY SIZE INTO RECORD-PREDICTION-FAIL
       .

       COMPUTE-ALL-FIELDS.
           PERFORM CALC-HAS-GRAMMAR
           PERFORM CALC-QUESTION
           PERFORM CALC-PREDICTED-BIOLOGICAL-LANGUAGE-CORE
           PERFORM CALC-BIO-HOCKETT-SCORE
           PERFORM CALC-IS-DESCRIPTION-OF
           PERFORM CALC-IS-OPEN-CLOSED-WORLD-CONFLICTED
           PERFORM CALC-RELATIONSHIP-TO-CONCEPT
           PERFORM CALC-PREDICTED-ANSWER
           PERFORM CALC-PREDICTED-BIOLOGICAL-LANGUAGE-STRICT
           PERFORM CALC-PREDICTION-PREDICATES
           PERFORM CALC-PREDICTION-FAIL
       .
       FIND-CONTAINS.
           MOVE "false" TO WS-FIND-RESULT
           MOVE 1 TO WS-FIND-I
           COMPUTE WS-FIND-LEN = FUNCTION LENGTH(WS-FIND-HAYSTACK)
           COMPUTE WS-FIND-NLEN = FUNCTION LENGTH(WS-FIND-NEEDLE)
           IF WS-FIND-NLEN = 0
               MOVE "true" TO WS-FIND-RESULT
           END-IF
           PERFORM UNTIL WS-FIND-I > WS-FIND-LEN - WS-FIND-NLEN + 1
               OR WS-FIND-RESULT = "true"
               IF WS-FIND-HAYSTACK(WS-FIND-I:WS-FIND-NLEN) = WS-FIND-NEEDLE
                   MOVE "true" TO WS-FIND-RESULT
               END-IF
               ADD 1 TO WS-FIND-I
           END-PERFORM
           .