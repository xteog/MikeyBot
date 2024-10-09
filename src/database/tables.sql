DROP DATABASE IF EXISTS `MikeyBot`;
CREATE DATABASE `MikeyBot`;
USE `MikeyBot`;

CREATE TABLE Users (
    `id` varchar(32) PRIMARY KEY,
    `nick` varchar(64) NOT NULL,
    `number` char(3)
);

CREATE TABLE Rules (
    `id` integer PRIMARY KEY,
    `name` varchar(256) NOT NULL,
    `code` varchar(16) NOT NULL,
    `description` TEXT NOT NULL,
    `escalation` integer NOT NULL,
    `de_escalation` integer NOT NULL
);

CREATE TABLE OffenceLevels (
    `offence` integer NOT NULL,
    `level` integer NOT NULL,
    `penalty` varchar(64) NOT NULL,
    `color` int NOT NULL,
    PRIMARY KEY (`offence`, `level`),
    FOREIGN KEY (`offence`) REFERENCES Rules(`id`) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Reports (
    `id` char(4) PRIMARY KEY,
    `sender` varchar(32) NOT NULL,
    `offender` varchar(32) NOT NULL,
    `league` varchar(8) NOT NULL,
    `season` integer NOT NULL,
    `round` integer NOT NULL,
    `description` TEXT NOT NULL,
    `rule` integer,
    `proof` varchar(128) NOT NULL,
    `penalty` varchar(128),
    `aggravated` BOOLEAN NOT NULL DEFAULT FALSE,
    `notes` TEXT,
    `active` BOOLEAN NOT NULL DEFAULT TRUE,
    `timestamp` DATETIME NOT NULL,
    FOREIGN KEY (`sender`) REFERENCES Users(`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (`offender`) REFERENCES Users(`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (`rule`) REFERENCES Rules(`id`) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Votes (
    `user` varchar(32) NOT NULL,
    `report` char(4) NOT NULL,
    `type` integer NOT NULL,
    `in_favor` boolean NOT NULL,
    PRIMARY KEY (`user`, `report`, `type`),
    FOREIGN KEY (`user`) REFERENCES Users(`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (`report`) REFERENCES Reports(`id`) ON UPDATE CASCADE ON DELETE CASCADE
);

INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (0, '(Unreasonable) Edging/Bumping/Leaving Lanes/Swerving/Sudden Lane Changes', 'H.1.1', "Any case where a driver would reasonably be expected to leave a lane for another driver but fails to do so, swerves excessively on a straight, suddenly changes lane or direction in a potentially unsafe manner, causes an avoidable, potentially dangerous colission, or otherwise can be considered responsible for another car being forced off-track.", 1, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (1, 'Divebombing', 'H.1.2', "Braking excessively late in an attempt to overtake, risking potentially pushing both themselves and/or other drivers off-track and/or causing a colission. While doing so safely may sometimes be possible, this is wholly up to the drivers responsibility.", 2, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (2, 'Unsafe Pit Entry/Unsafe Track Re-entry/Blocking', 'H.1.3', "Any case where a driver unsafely enters the Pit Lane (such as but not limited to risking forcing another car to also enter the pits), any case where a driver unsafely rejoins the track after going off-track or when exiting the pit lane, and any case where a driver moves into another cars line reactively and/or while going notably slower (as this potentially risks a rear-end colission).", 2, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (3, 'Chatting during a Race/ Spamming in Lobby Chat', 'H.1.4', "Any case of chatting during the race (outside of approved communication codes or other necessary communication), including during the countdown (when the leader has finished but other cars may still be racing), any excessive spamming while in the lobby, and excessively and/or unnecessarily leaving and rejoining the race or lobby during a race.", 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (4, 'Racing w/o valid CT', 'H.1.5', "Any case where a driver is found Post-Race to have been racing without a valid Connection Test, or an approved exception to the requirement of one. Any driver found to not have a valid CT completed, nor an approved exception, must complete a valid CT as approved by a Connection Officer or explicitly receive an exception (either temporary or permanent) before the race from either the Host or the URA.", 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (5, 'Severe Lag Issues/Teleporting', 'H.1.6', "Notable teleporting, stuttering, connection-caused disconnects, any any other connection-related issues, as well as any other technical problem causing similar issues. This category is not Escalated and De-escalated as others are, but is to be dealt with in whichever way is best to limit and resolve these issues while maintaining safety and competitive integrity.", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (6, 'Ignoring/Interfering with Officials', 'H.1.7', "Any case of a driver refusing to follow instructions from an Official 'in function', including off-track, in the lobby, and during the race, as well as any meaningful attempt to disrupt, unfairly influence, or undermine organisers, authorities, officials, communication, the overall organisation process of the Leagues or the process of hosting and running a race.", 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (7, 'Targeting a Driver', 'H.1.8', "Any deliberate action with the intent or purpose of unfairly interfering with or disrupting another drivers race, including any form of other kinds of Offenses, intentional negligence, or carelessness with such a purpose.", 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (8, 'Backwards Driving/Blocking the Finish Line Post-Race/Similar Offenses', 'H.1.9', "Any case of drivers driving in the opposite direction to the track (except when absolutely necessary, or while ghosted in the pit lane provided the driver enters and exits the pits as intended), unsafely parking the car when manually DNF'ing, or exiting the intended accessible track area.", 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (9, 'Failure To Follow 2CR (In CL Feature Races and Dry UL Races (w Rain set to 0%))', 'H.1.10', "Any case where drivers fail to field at least two different tyre compounds, in races where this is mandatory (CL Feature races and UL races where rain is disabled).", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (10, "Failure to Complete 80% of Race Winner's amount of Laps", 'H.1.11', "Any case where drivers fail to complete 80 percent of the race distance, or 80 percent of the race winners covered distance in the case of a red flag where the race can not be restarted.", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (11, 'Other (On-Track)', "H.1.13", "Any case of not-otherwise-classified dangerous driving, any severe on-track unsportsmanlike behavior, conspiracy to commit, and any on-track actions deemed significantly damaging or degrading to, violating the integrity of, or making a mockery of the League as a whole.", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (12, 'Other (Off-Track)', 'H.1.14', "Any form of severe unsportsmanlike behavior off-track, including aggression, attempted exploitation of a perceived loophole or exploit, hate speech, harrasment, abuse, severe personal attacks, spam, conspiracy to commit, abuse of power, and any off-track actions deemed significantly damaging or degrading to, violating the integrity of, or making a mockery of the League as a whole", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (13, 'Abusing Exploits or Bugs/Using Cheats', 'H.1.15', "Any meaningful attempt to use any form of external software, file manipulation, glitch or exploit within the game, perceived loophole, exploit or oversight within the League's Rules, or any other means of attempting to gain an unfair advantage.", 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (14, 'Alting/Impersonating', 'H.1.16', "Any case where a driver races, or attempts to race, under a different name (that isn't recognizable) without adequately communicating this new identity, a well as any attempt at impersonating another person both on- or off-track.", 0, 0);


INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 1, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 2, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 3, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 4, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 5, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 6, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 7, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (0, 8, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 1, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 2, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 3, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 4, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 5, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 6, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 7, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (1, 8, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 1, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 2, '2.5s Penalty', 0xFFE599);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 3, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 4, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 5, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 6, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 7, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (2, 8, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 1, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 2, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 3, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 4, '5s Penalty', 0xF9CB9C);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 5, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 6, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 7, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (3, 8, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 1, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 2, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 3, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 4, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 5, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 6, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 7, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (4, 8, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 0, 'Warning + Connection Rehab', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 1, 'Grid Penalty', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 2, 'Grid Penalty', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 3, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 4, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 5, 'Indefinite Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 6, 'Indefinite Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 7, 'Indefinite Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (5, 8, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 0, 'Warning', 0x93C47D);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 1, 'DQ/URA D (when Off-Track)', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 2, 'DQ/URA D (when Off-Track)', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 3, 'DQ/URA D (when Off-Track)', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 4, 'DQ/URA D (when Off-Track)', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 5, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 6, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 7, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (6, 8, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 0, '10s Penalty', 0xF6B26B);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 1, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 2, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 3, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 4, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 5, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 6, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 7, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (7, 8, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 0, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 1, 'DQ + Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 2, 'DQ + Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 3, 'DQ + Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 4, 'DQ + Race Ban', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 5, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 6, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 7, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (8, 8, 'DQ + Race Ban + URA D', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 0, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 1, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 2, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 3, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 4, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 5, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 6, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 7, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (9, 8, 'DQ', 0xEA9999);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 0, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 1, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 2, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 3, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 4, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 5, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 6, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 7, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (10, 8, 'Classified "From-The-Bottom-Up"', 0xD5A6BD);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 0, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 1, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 2, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 3, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 4, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 5, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 6, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 7, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (11, 8, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 0, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 1, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 2, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 3, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 4, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 5, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 6, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 7, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (12, 8, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 0, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 1, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 2, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 3, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 4, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 5, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 6, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 7, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (13, 8, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 0, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 1, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 2, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 3, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 4, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 5, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 6, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 7, 'URA Discretion', 0x000000);
INSERT INTO OffenceLevels (offence, level, penalty, color) VALUES (14, 8, 'URA Discretion', 0x000000);