#!/usr/bin/env bash
# Rôles PostgreSQL de TerangaCycle AI (AD-15), créés hors Alembic.
#
# Exécuté une seule fois par le superutilisateur, à la création du volume de données
# (docker-entrypoint-initdb.d). Mots de passe lus dans /run/secrets/.
#   - teranga_migrator : propriétaire du schéma public, exécute les migrations ;
#   - teranga_app      : CONNECT, USAGE et DML seulement (API et worker).
set -eo pipefail

read_secret() {
	local file="/run/secrets/$1"
	if [ ! -f "$file" ] || [ ! -s "$file" ]; then
		echo "20-roles.sh : secret manquant ou vide : $file" >&2
		exit 1
	fi
	tr -d '\r\n' < "$file"
}

migrator_password="$(read_secret db_migrator_password)"
app_password="$(read_secret db_app_password)"

psql -v ON_ERROR_STOP=1 \
	--username "$POSTGRES_USER" \
	--dbname "$POSTGRES_DB" \
	--set db="$POSTGRES_DB" \
	--set migrator_password="$migrator_password" \
	--set app_password="$app_password" <<-'EOSQL'
	CREATE ROLE teranga_migrator LOGIN PASSWORD :'migrator_password';
	CREATE ROLE teranga_app LOGIN PASSWORD :'app_password';

	-- Personne d'autre ne se connecte à la base.
	REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
	GRANT CONNECT, TEMPORARY ON DATABASE :"db" TO teranga_migrator;
	GRANT CONNECT ON DATABASE :"db" TO teranga_app;

	-- Le schéma public appartient au rôle de migration ; l'application ne peut qu'y lire.
	ALTER SCHEMA public OWNER TO teranga_migrator;
	REVOKE ALL ON SCHEMA public FROM PUBLIC;
	GRANT USAGE ON SCHEMA public TO teranga_app;

	-- Tables et séquences créées par les futures migrations : DML pour l'application.
	ALTER DEFAULT PRIVILEGES FOR ROLE teranga_migrator IN SCHEMA public
		GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO teranga_app;
	ALTER DEFAULT PRIVILEGES FOR ROLE teranga_migrator IN SCHEMA public
		GRANT USAGE, SELECT ON SEQUENCES TO teranga_app;
EOSQL
