# Hangman-Demo Rulebook Specification Document

## Overview
This document provides a detailed specification for the "Hangman-Demo" rulebook, which is structured to manage player data and game statistics for a hangman game. The rulebook includes various entities such as Players, Games, Categories, Words, and Levels, each with specific fields and calculated metrics. The calculated fields derive insights from the raw data, enabling a better understanding of player performance and game dynamics.

## Players Entity

### Input Fields
1. **PlayerId**
   - **Type:** String
   - **Description:** Unique identifier for each player.

2. **Name**
   - **Type:** String
   - **Description:** The name of the player.

3. **PlayerName**
   - **Type:** String
   - **Description:** The display name of the player.

4. **EmailAddress**
   - **Type:** String
   - **Description:** The email address of the player.

5. **Games**
   - **Type:** String (relationship)
   - **Description:** A list of games associated with the player.

### Calculated Fields
1. **CountOfGamesPlayed**
   - **Description:** This field counts the total number of games played by the player.
   - **Calculation:** Count the number of entries in the Games field that match the PlayerId.
   - **Formula:** `=COUNTIFS(Games!{{Player}}, Players!{{PlayerId}})`
   - **Example:** For player Alice (PlayerId: `p001`), the CountOfGamesPlayed is `1` because she has played one game (`alice-tiger`).

2. **HasPlayedALot**
   - **Description:** This field indicates whether the player has played 15 or more games.
   - **Calculation:** Check if CountOfGamesPlayed is greater than or equal to 15.
   - **Formula:** `={{CountOfGamesPlayed}} >= 15`
   - **Example:** For player Linda (CountOfGamesPlayed: `16`), HasPlayedALot is `true` because she has played more than 15 games.

3. **CanComment**
   - **Description:** This field indicates whether the player can leave comments based on their game participation.
   - **Calculation:** Check if CountOfGamesPlayed is greater than 3.
   - **Formula:** `={{CountOfGamesPlayed}}>3`
   - **Example:** For player Bob (CountOfGamesPlayed: `10`), CanComment is `true` because he has played more than 3 games.

4. **CountOfWins**
   - **Description:** This field counts the total number of wins for the player.
   - **Calculation:** Count the number of games where IsWin is true for the player.
   - **Formula:** `=COUNTIFS(Games!{{Player}}, Players!{{PlayerId}})`
   - **Example:** For player Linda, CountOfWins is `1` because she won one game (`linda-tiger`).

## Games Entity

### Input Fields
1. **GameId**
   - **Type:** String
   - **Description:** Unique identifier for each game.

2. **Player**
   - **Type:** String (relationship)
   - **Description:** The player associated with the game.

3. **Word**
   - **Type:** String (relationship)
   - **Description:** The word used in the game.

4. **IsWin**
   - **Type:** Boolean
   - **Description:** Indicates whether the player won the game.

### Calculated Fields
1. **Name**
   - **Description:** This field constructs the name of the game by combining the player's name and the word used.
   - **Calculation:** Concatenate PlayerName with WordName, separated by a hyphen.
   - **Formula:** `={{PlayerName}} & "-" & {{WordName}}`
   - **Example:** For the game `linda-tiger`, the Name is `Linda-Tiger`.

2. **PlayerName**
   - **Description:** This field retrieves the name of the player associated with the game.
   - **Calculation:** Look up the PlayerName based on the Player's ID.
   - **Formula:** `=INDEX(Players!{{PlayerName}}, MATCH(Games!{{Player}}, Players!{{PlayerId}}, 0))`
   - **Example:** For the game `bob-test`, the PlayerName is `Bob`.

3. **PlayerEmailAddress**
   - **Description:** This field retrieves the email address of the player associated with the game.
   - **Calculation:** Look up the EmailAddress based on the Player's ID.
   - **Formula:** `=INDEX(Players!{{EmailAddress}}, MATCH(Games!{{Player}}, Players!{{PlayerId}}, 0))`
   - **Example:** For the game `linda-tiger`, the PlayerEmailAddress is `linda@ssot.me`.

4. **WordName**
   - **Description:** This field retrieves the name of the word used in the game.
   - **Calculation:** Look up the WordName based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{Name}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the WordName is `Tiger`.

5. **CategoryName**
   - **Description:** This field retrieves the category name of the word used in the game.
   - **Calculation:** Look up the CategoryName based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{CategoryName}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the CategoryName is `Animals`.

6. **LevelName**
   - **Description:** This field retrieves the level name of the word used in the game.
   - **Calculation:** Look up the LevelName based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{LevelName}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the LevelName is `Easy`.

7. **LevelDescription**
   - **Description:** This field retrieves the description of the level of the word used in the game.
   - **Calculation:** Look up the LevelDescription based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{LevelDescription}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the LevelDescription is `This is an easy word - common, etc`.

8. **LevelMinLength**
   - **Description:** This field retrieves the minimum length of the word used in the game.
   - **Calculation:** Look up the LevelMinLength based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{LevelMinLength}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the LevelMinLength is `3`.

9. **LevelMaxLength**
   - **Description:** This field retrieves the maximum length of the word used in the game.
   - **Calculation:** Look up the LevelMaxLength based on the Word's ID.
   - **Formula:** `=INDEX(Words!{{LevelMaxLength}}, MATCH(Games!{{Word}}, Words!{{WordId}}, 0))`
   - **Example:** For the game `bob-tiger`, the LevelMaxLength is `5`.

## Conclusion
This specification outlines the structure and calculations for the Hangman-Demo rulebook, detailing how to derive calculated fields from raw input data. By following the provided formulas and examples, one can accurately compute the values necessary for player and game analysis.