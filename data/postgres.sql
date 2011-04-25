--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: plpgsql; Type: PROCEDURAL LANGUAGE; Schema: -; Owner: wardbu
--

CREATE PROCEDURAL LANGUAGE plpgsql;


ALTER PROCEDURAL LANGUAGE plpgsql OWNER TO wardbu;

SET search_path = public, pg_catalog;

--
-- Name: set_create_times(); Type: FUNCTION; Schema: public; Owner: wardbu
--

CREATE FUNCTION set_create_times() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.created_at := CURRENT_TIMESTAMP;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_create_times() OWNER TO wardbu;

--
-- Name: set_update_time(); Type: FUNCTION; Schema: public; Owner: wardbu
--

CREATE FUNCTION set_update_time() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
  END;
$$;


ALTER FUNCTION public.set_update_time() OWNER TO wardbu;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: tokens; Type: TABLE; Schema: public; Owner: wardbu; Tablespace: 
--

CREATE TABLE tokens (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    token character varying(32) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tokens OWNER TO wardbu;

--
-- Name: token_id_seq; Type: SEQUENCE; Schema: public; Owner: wardbu
--

CREATE SEQUENCE token_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.token_id_seq OWNER TO wardbu;

--
-- Name: token_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wardbu
--

ALTER SEQUENCE token_id_seq OWNED BY tokens.id;


--
-- Name: token_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wardbu
--

SELECT pg_catalog.setval('token_id_seq', 1, true);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: wardbu
--

ALTER TABLE tokens ALTER COLUMN id SET DEFAULT nextval('token_id_seq'::regclass);


--
-- Data for Name: tokens; Type: TABLE DATA; Schema: public; Owner: wardbu
--

COPY tokens (id, username, token, created_at, updated_at) FROM stdin;
\.


--
-- Name: primary_id; Type: CONSTRAINT; Schema: public; Owner: wardbu; Tablespace: 
--

ALTER TABLE ONLY tokens
    ADD CONSTRAINT primary_id PRIMARY KEY (id);


--
-- Name: username_unique_id; Type: CONSTRAINT; Schema: public; Owner: wardbu; Tablespace: 
--

ALTER TABLE ONLY tokens
    ADD CONSTRAINT username_unique_id UNIQUE (username);


--
-- Name: update_token; Type: RULE; Schema: public; Owner: wardbu
--

CREATE RULE update_token AS ON INSERT TO tokens WHERE (EXISTS (SELECT 1 FROM tokens token WHERE ((token.username)::text = (new.username)::text))) DO INSTEAD UPDATE tokens SET token = new.token WHERE ((token.username)::text = (new.username)::text);


--
-- Name: set_create_times_tr; Type: TRIGGER; Schema: public; Owner: wardbu
--

CREATE TRIGGER set_create_times_tr
    BEFORE INSERT ON tokens
    FOR EACH ROW
    EXECUTE PROCEDURE set_create_times();


--
-- Name: set_update_time_tr; Type: TRIGGER; Schema: public; Owner: wardbu
--

CREATE TRIGGER set_update_time_tr
    BEFORE UPDATE ON tokens
    FOR EACH ROW
    EXECUTE PROCEDURE set_update_time();


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

