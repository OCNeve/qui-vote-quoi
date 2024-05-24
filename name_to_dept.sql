

WITH age_filtered_occurences AS (
    SELECT
        po.departement_id,
        po.compte,
        po.prenom_id,
        po.annee_id,
        p.valeur AS prenom,
        a.valeur AS annee
    FROM
        voters.prenoms_occurences po
        JOIN voters.prenoms p ON po.prenom_id = p.id
        JOIN voters.annees a ON po.annee_id = a.id
    WHERE
        p.valeur = 'DAVID'  -- Replace 'given_prenom' with the actual name
        AND a.valeur ~ '^\d{4}$'  -- Ensure valid year entries
        AND a.valeur::INTEGER BETWEEN (EXTRACT(YEAR FROM CURRENT_DATE) - 25) AND (EXTRACT(YEAR FROM CURRENT_DATE) - 15)
),
departement_total AS (
    SELECT
        po.departement_id,
        SUM(po.compte) AS total_compte
    FROM
        voters.prenoms_occurences po
        JOIN voters.annees a ON po.annee_id = a.id
    WHERE
        a.valeur ~ '^\d{4}$'  -- Ensure valid year entries
        AND a.valeur::INTEGER BETWEEN (EXTRACT(YEAR FROM CURRENT_DATE) - 25) AND (EXTRACT(YEAR FROM CURRENT_DATE) - 15)
    GROUP BY
        po.departement_id
),
prenoms_ratio AS (
    SELECT
        afo.departement_id,
        SUM(afo.compte) AS prenom_total,
        dt.total_compte,
        SUM(afo.compte)::FLOAT / dt.total_compte AS ratio
    FROM
        age_filtered_occurences afo
        JOIN departement_total dt ON afo.departement_id = dt.departement_id
    GROUP BY
        afo.departement_id, dt.total_compte
)
SELECT
    d.nom AS departement_name,
	d.numero,
    pr.departement_id,
    pr.prenom_total,
    pr.total_compte,
    pr.ratio
FROM
    prenoms_ratio pr
    JOIN voters.departements d ON pr.departement_id = d.id
WHERE
    d.numero ~ '^\d{2,3}$'  -- Ensure valid department entries
	and d.numero::int < 100 -- Avoid domtoms
ORDER BY
    pr.ratio DESC
LIMIT 1;  -- Returns the department with the highest ratio
