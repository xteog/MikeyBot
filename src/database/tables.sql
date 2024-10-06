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

INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (0, '(Unreasonable) Edging/Bumping/Leaving Lanes/Swerving/Sudden Lane Changes', 'H.1.3', "Slowly closing off someone's lane, tackling or steering into/around them on straight so that it takes away their claimed racing line or removes them from the track. This includes abrupt and erratic lane changes and movements, brake checks, or defending causing contact, and impeding.", 1, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (1, 'Divebombing', 'H.1.5', "Entering a corner with late breaking, or no braking, in which the driver makes contact with, or aggressively attacks another driver putting them at risk of ruining their line of racing through turn, instead of taking a known or safe racing line through a turn. A divebomb pass can be done safely, but is wholly at the driver's responsibility to keep it safe. A late-Break is considered an accidental form of divebomb, but is still the responsibility of the driver.", 2, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (2, 'Unsafe Pit Entry/Unsafe Track Re-entry/Blocking', 'H.1.2', "Any violation of Pitting Code (G.2.2) or failure to return to track safely or staying in the entry/exit lane of the pits until safe to do otherwise. Failure to get into the exit side of the track safely ahead of the pit entry lane. Cutting across lanes with traffic, into faster traffic, and not allowing faster vehicles to pass, on any other unsafe motions involved in entering/exiting the track.", 2, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (3, 'Chatting during a Race/ Spamming in Lobby Chat', 'H.1.1', 'Failure to use approved communication / codes, and talking in any capacity during the race or after the flag while others are still racing', 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (4, 'Racing w/o valid CT', '', '', 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (5, 'Severe Lag Issues/Teleporting', '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (6, 'Ignoring/Interfering with Officials', '', '', 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (7, 'Targeting a Driver', '', '', 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (8, 'Backwards Driving/Blocking the Finish Line Post-Race/Similar Offenses', '', '', 4, 1);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (9, 'Failure To Follow 2CR (In CL Feature Races and Dry UL Races (w Rain set to 0%))', '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (10, "Failure to Complete 80% of Race Winner's amount of Laps", '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (11, 'Other (On-Track)', '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (12, 'Other (Off-Track)', '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (13, 'Abusing Exploits or Bugs/Using Cheats', '', '', 0, 0);
INSERT INTO Rules (id, name, code, description, escalation, de_escalation)
VALUES (14, 'Alting/Impersonating', '', '', 0, 0);

CREATE TABLE OffenceLevels (
    `offence` integer NOT NULL,
    `level` integer NOT NULL,
    `penalty` varchar(64) NOT NULL,
    PRIMARY KEY (`offence`, `level`),
    FOREIGN KEY (`offence`) REFERENCES Rules (`id`) ON UPDATE CASCADE ON DELETE CASCADE
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
    `proof` varchar(64) NOT NULL,
    `penalty` varchar(128),
    `aggravated` BOOLEAN,
    `notes` TEXT,
    `active` BOOLEAN DEFAULT TRUE,
    `timestamp` DATETIME NOT NULL,
    FOREIGN KEY (`sender`) REFERENCES Users(`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (`offender`) REFERENCES Users(`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (`rule`) REFERENCES Rules(`id`) ON UPDATE CASCADE ON DELETE CASCADE
);

INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 1, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 2, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 3, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 4, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 5, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 6, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 7, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (0, 8, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 1, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 2, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 3, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 4, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 5, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 6, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 7, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (1, 8, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 1, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 2, '2.5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 3, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 4, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 5, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 6, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 7, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (2, 8, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 1, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 2, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 3, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 4, '5s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 5, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 6, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 7, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (3, 8, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 1, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 2, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 3, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 4, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 5, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 6, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 7, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (4, 8, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 0, 'Warning + Connection Rehab');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 1, 'Grid Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 2, 'Grid Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 3, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 4, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 5, 'Indefinite Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 6, 'Indefinite Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 7, 'Indefinite Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (5, 8, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 0, 'Warning');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 1, 'DQ/URA D (when Off-Track)');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 2, 'DQ/URA D (when Off-Track)');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 3, 'DQ/URA D (when Off-Track)');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 4, 'DQ/URA D (when Off-Track)');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 5, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 6, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 7, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (6, 8, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 0, '10s Penalty');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 1, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 2, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 3, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 4, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 5, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 6, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 7, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (7, 8, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 0, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 1, 'DQ + Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 2, 'DQ + Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 3, 'DQ + Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 4, 'DQ + Race Ban');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 5, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 6, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 7, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (8, 8, 'DQ + Race Ban + URA D');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 0, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 1, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 2, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 3, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 4, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 5, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 6, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 7, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (9, 8, 'DQ');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 0, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 1, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 2, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 3, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 4, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 5, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 6, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 7, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (10, 8, 'Classified "From-The-Bottom-Up"');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 0, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 1, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 2, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 3, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 4, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 5, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 6, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 7, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (11, 8, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 0, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 1, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 2, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 3, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 4, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 5, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 6, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 7, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (12, 8, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 0, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 1, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 2, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 3, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 4, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 5, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 6, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 7, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (13, 8, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 0, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 1, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 2, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 3, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 4, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 5, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 6, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 7, 'URA Discretion');
INSERT INTO OffenceLevels (offence, level, penalty) VALUES (14, 8, 'URA Discretion');