BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "scrap_date" (
	"id"	INTEGER NOT NULL,
	"dates"	DATE,
	"research_id"	INTEGER,
	FOREIGN KEY("research_id") REFERENCES "research"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "research" (
	"id"	INTEGER NOT NULL,
	"company_name"	VARCHAR(128) NOT NULL,
	"linkedin_presence"	INTEGER NOT NULL,
	"region"	VARCHAR(64) NOT NULL,
	"industry"	VARCHAR(128) NOT NULL,
	"note"	TEXT NOT NULL,
	"email_format"	VARCHAR(64) NOT NULL,
	"format_name"	VARCHAR(128) NOT NULL,
	"format_type"	VARCHAR(128) NOT NULL,
	"other_email_format"	VARCHAR(64) NOT NULL,
	"total_count"	INTEGER NOT NULL,
	"domain"	VARCHAR(128) NOT NULL,
	"research_date"	DATE NOT NULL,
	"countries"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"email"	VARCHAR(64),
	"username"	VARCHAR(64),
	"role_id"	INTEGER,
	"password_hash"	VARCHAR(128),
	FOREIGN KEY("role_id") REFERENCES "roles"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "scrap" (
	"id"	INTEGER NOT NULL,
	"country"	VARCHAR(64) NOT NULL,
	"email"	VARCHAR(64) NOT NULL,
	"first_name"	VARCHAR(128) NOT NULL,
	"last_name"	VARCHAR(128) NOT NULL,
	"industry"	VARCHAR(128) NOT NULL,
	"validity_grade"	VARCHAR(64) NOT NULL,
	"link"	TEXT NOT NULL,
	"position"	TEXT NOT NULL,
	"blast_date"	DATE,
	"upload_date"	DATE NOT NULL,
	"percentage"	INTEGER NOT NULL,
	"unblasted"	BOOLEAN NOT NULL,
	"sent"	BOOLEAN NOT NULL,
	"delivered"	BOOLEAN NOT NULL,
	"soft_bounces"	BOOLEAN NOT NULL,
	"hard_bounces"	BOOLEAN NOT NULL,
	"opened"	BOOLEAN NOT NULL,
	"unsubscribed"	BOOLEAN NOT NULL,
	"company_name"	TEXT NOT NULL,
	CHECK(unsubscribed IN (0,1)),
	CHECK(opened IN (0,1)),
	CHECK(hard_bounces IN (0,1)),
	CHECK(soft_bounces IN (0,1)),
	CHECK(delivered IN (0,1)),
	CHECK(sent IN (0,1)),
	CHECK(unblasted IN (0,1)),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "roles" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(64) UNIQUE,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num"	VARCHAR(32) NOT NULL,
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_research_company_name" ON "research" (
	"company_name"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_username" ON "users" (
	"username"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_email" ON "users" (
	"email"
);
CREATE INDEX IF NOT EXISTS "ix_scrap_company_name" ON "scrap" (
	"company_name"
);
CREATE INDEX IF NOT EXISTS "ix_scrap_country" ON "scrap" (
	"country"
);
COMMIT;
