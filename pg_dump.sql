--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.19
-- Dumped by pg_dump version 9.6.19

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE kenwood; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE kenwood IS 'kenwood VHF radio data';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: qt_frequencies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.qt_frequencies (
    qt_freq double precision NOT NULL
);


ALTER TABLE public.qt_frequencies OWNER TO postgres;

--
-- Name: tk_channels; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tk_channels (
    channel_id character varying(60) NOT NULL,
    freq_tx double precision,
    freq_rx double precision,
    qt_tx double precision,
    qt_rx double precision,
    power boolean DEFAULT true,
    scan boolean DEFAULT true,
    width boolean DEFAULT false,
    description text
);


ALTER TABLE public.tk_channels OWNER TO postgres;

--
-- Name: COLUMN tk_channels.power; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tk_channels.power IS 'High / Low';


--
-- Name: COLUMN tk_channels.scan; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tk_channels.scan IS 'Yes / No';


--
-- Name: COLUMN tk_channels.width; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tk_channels.width IS 'Wide / Narrow';


--
-- Name: qt_frequencies qt_frequencies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qt_frequencies
    ADD CONSTRAINT qt_frequencies_pkey PRIMARY KEY (qt_freq);


--
-- Name: tk_channels tk_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tk_channels
    ADD CONSTRAINT tk_channels_pkey PRIMARY KEY (channel_id);


--
-- PostgreSQL database dump complete
--

