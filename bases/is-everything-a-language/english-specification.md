# Specification Document for Rulebook: PUBLISHED - ERB_semiotics-is-everything-a-language

## Overview
This rulebook provides a structured approach to classify various language candidates based on specific attributes. It includes a set of calculated fields that derive insights from raw data about each candidate, helping to determine whether a given candidate qualifies as a language. The rulebook is generated from an Airtable base and includes detailed definitions, predicates, and examples for clarity.

## LanguageCandidates Entity

### Input Fields
1. **LanguageCandidateId**
   - **Type:** string
   - **Description:** Unique identifier for the language candidate.

2. **Name**
   - **Type:** string
   - **Description:** Name of the language candidate being classified.

3. **IsLanguage**
   - **Type:** boolean
   - **Description:** Indicates if the candidate is considered a language.

4. **HasSyntax**
   - **Type:** boolean
   - **Description:** Indicates if the language candidate has syntax and/or grammar.

5. **CanBeHeld**
   - **Type:** boolean
   - **Description:** Indicates if the candidate is physical/material.

6. **DistanceFromConcept**
   - **Type:** integer
   - **Description:** Numeric value representing the distance from a conceptual reference.

### Calculated Fields

1. **HasGrammar**
   - **Description:** Determines if the candidate has grammar based on the presence of syntax.
   - **Calculation:** If `HasSyntax` is true, then `HasGrammar` is true.
   - **Formula:** `={{HasSyntax}} = TRUE()`
   - **Example:** If `HasSyntax` for "English" is true, then `HasGrammar` will also be true.

2. **Question**
   - **Description:** Constructs a question that could be posed to a survey audience regarding the language candidate.
   - **Calculation:** Concatenates the phrase "Is " with the candidate's `Name` and " a language?".
   - **Formula:** `="Is " & {{Name}} & " a language?"`
   - **Example:** For "English", the question would be "Is English a language?".

3. **PredictedAnswer**
   - **Description:** Predicts if the candidate is likely to be considered a language based on multiple attributes.
   - **Calculation:** Returns true if all of the following conditions are met:
     - `HasSyntax` is true
     - `IsParsed` is true
     - `IsDescriptionOf` is true
     - `HasLinearDecodingPressure` is true
     - `ResolvesToAnAST` is true
     - `IsStableOntologyReference` is true
     - `CanBeHeld` is false
     - `HasIdentity` is false
   - **Formula:** `=AND({{HasSyntax}}, {{IsParsed}}, {{IsDescriptionOf}}, {{HasLinearDecodingPressure}}, {{ResolvesToAnAST}}, {{IsStableOntologyReference}}, NOT({{CanBeHeld}}), NOT({{HasIdentity}}))`
   - **Example:** For "English", all conditions are true, so `PredictedAnswer` is true.

4. **PredictionPredicates**
   - **Description:** Summarizes the predicates that contribute to the prediction of the candidate being a language.
   - **Calculation:** Concatenates the results of various checks into a descriptive string.
   - **Formula:** 
     ```
     =IF({{HasSyntax}}, "Has Syntax", "No Syntax") & " & " & 
     IF({{IsParsed}}, "Requires Parsing", "No Parsing Needed") & " & " & 
     IF({{IsDescriptionOf}}, "Describes the thing", "Is the Thing") & " & " & 
     IF({{HasLinearDecodingPressure}}, "Has Linear Decoding Pressure", "No Decoding Pressure") & " & " & 
     IF({{ResolvesToAnAST}}, "Resolves to AST", "No AST") & ", " & 
     IF({{IsStableOntologyReference}}, "Is Stable Ontology", "Not 'Ontology'") & " AND " & 
     IF({{CanBeHeld}}, "Can Be Held", "Can't Be Held") & ", " & 
     IF({{HasIdentity}}, "Has Identity", "Has no Identity")
     ```
   - **Example:** For "English", the predicates would yield: "Has Syntax & Requires Parsing & Describes the thing & Has Linear Decoding Pressure & Resolves to AST, Is Stable Ontology AND Can't Be Held, Has no Identity".

5. **PredictionFail**
   - **Description:** Provides an explanation if the predicted answer does not match the candidate's status.
   - **Calculation:** If `PredictedAnswer` does not equal `IsLanguage`, it constructs a message explaining the mismatch.
   - **Formula:** 
     ```
     =IF(NOT({{PredictedAnswer}} = {{IsLanguage}}), 
       {{Name}} & " " & IF({{PredictedAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
       IF({{IsLanguage}}, "Is", "Is Not") & " marked as a 'Language Candidate.'", "") & 
       IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.", "")
     ```
   - **Example:** For "A Coffee Mug", since `PredictedAnswer` is false and `IsLanguage` is true, the message would be: "A Coffee Mug Isn't a Family Feud Language, but Is marked as a 'Language Candidate.'".

6. **IsDescriptionOf**
   - **Description:** Determines if the candidate describes a concept based on its distance from that concept.
   - **Calculation:** Returns true if `DistanceFromConcept` is greater than 1.
   - **Formula:** `={{DistanceFromConcept}} > 1`
   - **Example:** For "English" with a `DistanceFromConcept` of 2, `IsDescriptionOf` will be true.

7. **IsOpenClosedWorldConflicted**
   - **Description:** Checks if both `IsOpenWorld` and `IsClosedWorld` are true, indicating a conflict.
   - **Calculation:** Returns true if both conditions are true.
   - **Formula:** `=AND({{IsOpenWorld}}, {{IsClosedWorld}})`
   - **Example:** If both `IsOpenWorld` and `IsClosedWorld` for "Falsifier A" are true, then `IsOpenClosedWorldConflicted` will be true.

8. **RelationshipToConcept**
   - **Description:** Identifies the relationship of the candidate to a concept based on `DistanceFromConcept`.
   - **Calculation:** Returns "IsMirrorOf" if `DistanceFromConcept` is 1, otherwise returns "IsDescriptionOf".
   - **Formula:** `=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`
   - **Example:** For "A Coffee Mug" with a `DistanceFromConcept` of 1, `RelationshipToConcept` will be "IsMirrorOf".

## Conclusion
This specification outlines how to compute various calculated fields for language candidates based on their raw attributes. By following the provided formulas and examples, one can accurately derive the necessary values for classification within the context of this rulebook.