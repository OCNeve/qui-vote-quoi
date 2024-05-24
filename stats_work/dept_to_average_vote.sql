WITH department_votes AS (
    SELECT
        v.candidat_fk,
        SUM(v.compte_votes) AS total_votes
    FROM
        voters.votes_par_departements v
        JOIN voters.departements d ON v.departement_id = d.id
    WHERE
        d.numero = '$DEPT$'
    GROUP BY
        v.candidat_fk
)
SELECT
    c.nom AS candidate_name,
    c.prenom AS candidate_firstname,
    dv.total_votes
FROM
    department_votes dv
    JOIN voters.candidats c ON dv.candidat_fk = c.id
ORDER BY
    dv.total_votes DESC
LIMIT 5; -- Returns the candidate with the most votes in the given department
