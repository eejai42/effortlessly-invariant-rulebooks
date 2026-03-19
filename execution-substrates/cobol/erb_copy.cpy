       *> ERB Record Layout (GENERATED - DO NOT EDIT)
       *> COPY "erb_copy" in erb_calc.cbl
       01 RECORD.

          02 SHAPE-ID PIC X(500).
          02 NAME PIC X(500).
          02 SIDES PIC X(500).
          02 HOW-MANY-SIDES PIC 9(10).
          02 SUM-OF-INTERNAL-ANGLES PIC X(500).
          02 MAX-ANGLE PIC X(500).
          02 HYPOTENUSE-LENGTH-SQUARED PIC X(500).
          02 NON-HYPOTENUSE-SIDES-SQUARED PIC X(500).
          02 IS-RECTANGLE PIC X(5).
          02 IS-TRIANGLE PIC X(5).
          02 IS-RIGHT-TRIANGLE PIC X(5).
          02 PYTHAGOREAN-THEOREM-HOLDS PIC X(5).