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

       *> ========== WORKFLOWS ==========
       *> Level 1
       CALC-NAME.
           *> ERROR: Could not parse formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")...
           MOVE "ERROR" TO RECORD-NAME
       .

       *> Level 2
       CALC-HAS-MORE-THAN1-STEP.
           IF RECORD-COUNT-OF-NON-PROPOSED-STEPS > 1
              MOVE "true" TO RECORD-HAS-MORE-THAN1-STEP
           ELSE
              MOVE "false" TO RECORD-HAS-MORE-THAN1-STEP
           END-IF
       .

       COMPUTE-ALL-FIELDS.
           PERFORM CALC-NAME
           PERFORM CALC-HAS-MORE-THAN1-STEP
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