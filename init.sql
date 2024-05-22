CREATE USER dev_user WITH PASSWORD 'masterkey';

CREATE DATABASE voters;

\c voters

CREATE SCHEMA voters;

GRANT ALL PRIVILEGES ON SCHEMA voters TO dev_user;

SET search_path TO voters;



CREATE TABLE voters.departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    numero VARCHAR(4) NOT NULL
);

CREATE TABLE voters.annees (
    id SERIAL PRIMARY KEY,
    valeur VARCHAR(4) NOT NULL
);


CREATE TABLE voters.prenoms (
    id SERIAL PRIMARY KEY,
    valeur VARCHAR(100) NOT NULL
);

CREATE TABLE voters.prenoms_occurences (
    id SERIAL PRIMARY KEY,
    departement_id INTEGER NOT NULL,
    annee_id INTEGER NOT NULL,
    prenom_id INTEGER NOT NULL,
    compte INTEGER NOT NULL,
    CONSTRAINT fk_departement_id
        FOREIGN KEY (departement_id)
        REFERENCES departements (id),
    CONSTRAINT fk_annee_id
        FOREIGN KEY (annee_id)
        REFERENCES annees (id),
    CONSTRAINT fk_prenom_id
        FOREIGN KEY (prenom_id)
        REFERENCES prenoms (id),
    CONSTRAINT unique_annee_dept_prenom
        UNIQUE (departement_id, annee_id)
);

CREATE TABLE voters.candidats (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255) NOT NULL
);

CREATE TABLE voters.votes_par_departements (
    id SERIAL PRIMARY KEY,
    candidat_fk INTEGER NOT NULL,
    departement_id INTEGER NOT NULL,
    compte_votes INTEGER NOT NULL,
    compte_inscrit INTEGER NOT NULL,
    CONSTRAINT fk_candidat_id
        FOREIGN KEY (candidat_fk)
        REFERENCES candidats (id),
    CONSTRAINT fk_departement_id
        FOREIGN KEY (departement_id)
        REFERENCES departements (id)
);



GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA voters TO dev_user;

COMMIT;