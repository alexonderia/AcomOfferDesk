--
-- PostgreSQL database dump
--

\restrict zWlfAqg2bNMLaw4u35il6ZvAOWL38AV6PkQPP7rhniXV6Qon8fhQbQaGAYV7N4B

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

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
-- Data for Name: job; Type: TABLE DATA; Schema: cron; Owner: order_admin
--

INSERT INTO cron.job (jobid, schedule, command, nodename, nodeport, database, username, active, jobname) VALUES (1, '1 0 * * *', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'localhost', 5432, 'order_database', 'order_admin', true, 'deadline_to_review_daily');


--
-- Data for Name: job_run_details; Type: TABLE DATA; Schema: cron; Owner: order_admin
--

INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 28, 3887635, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 2', '2026-04-28 03:01:00.020234+03', '2026-04-28 03:01:00.033062+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 18, 2410085, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-18 03:01:00.02636+03', '2026-04-18 03:01:00.032699+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 8, 959251, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 2', '2026-04-08 03:01:00.010971+03', '2026-04-08 03:01:00.017732+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 1, 68170, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-01 03:01:00.018752+03', '2026-04-01 03:01:00.020541+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 14, 1835629, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 1', '2026-04-14 03:01:00.014609+03', '2026-04-14 03:01:00.026882+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 2, 120738, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-02 03:01:00.016212+03', '2026-04-02 03:01:00.018132+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 9, 1098903, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-09 03:01:00.020405+03', '2026-04-09 03:01:00.026079+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 3, 260333, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-03 03:01:00.020385+03', '2026-04-03 03:01:00.026745+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 32, 296430, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-02 03:01:00.023633+03', '2026-05-02 03:01:00.028881+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 22, 3001167, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-22 03:01:00.025828+03', '2026-04-22 03:01:00.032308+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 4, 399893, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-04 03:01:00.017206+03', '2026-04-04 03:01:00.022801+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 10, 1238600, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-10 03:01:00.025625+03', '2026-04-10 03:01:00.033972+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 15, 1987720, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-15 03:01:00.018042+03', '2026-04-15 03:01:00.024554+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 5, 539750, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-05 03:01:00.02435+03', '2026-04-05 03:01:00.028675+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 19, 2562316, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-19 03:01:00.016938+03', '2026-04-19 03:01:00.021118+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 11, 1378272, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-11 03:01:00.026398+03', '2026-04-11 03:01:00.035118+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 6, 679453, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-06 03:01:00.013122+03', '2026-04-06 03:01:00.018972+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 7, 819313, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 1', '2026-04-07 03:01:00.028179+03', '2026-04-07 03:01:00.032444+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 16, 2127443, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-16 03:01:00.019445+03', '2026-04-16 03:01:00.026865+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 12, 1529749, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-12 03:01:00.012675+03', '2026-04-12 03:01:00.018646+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 25, 3450291, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 1', '2026-04-25 03:01:00.023208+03', '2026-04-25 03:01:00.040801+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 20, 2707879, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-20 03:01:00.014857+03', '2026-04-20 03:01:00.018491+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 13, 1669408, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-13 03:01:00.012796+03', '2026-04-13 03:01:00.016282+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 17, 2267235, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-17 03:01:00.020274+03', '2026-04-17 03:01:00.028587+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 27, 3741660, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-27 03:01:00.018793+03', '2026-04-27 03:01:00.02579+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 23, 3146944, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-23 03:01:00.028262+03', '2026-04-23 03:01:00.037517+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 21, 2853597, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-21 03:01:00.04074+03', '2026-04-21 03:01:00.047373+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 26, 3596030, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-26 03:01:00.020805+03', '2026-04-26 03:01:00.027206+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 24, 3304600, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-24 03:01:00.014235+03', '2026-04-24 03:01:00.015923+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 33, 441931, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-03 03:01:00.021121+03', '2026-05-03 03:01:00.026244+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 30, 4180870, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-30 03:01:00.029135+03', '2026-04-30 03:01:00.034302+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 29, 4033102, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-04-29 03:01:00.020525+03', '2026-04-29 03:01:00.02793+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 31, 150836, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-01 03:01:00.027262+03', '2026-05-01 03:01:00.03167+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 34, 587391, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-04 03:01:00.017214+03', '2026-05-04 03:01:00.02257+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 35, 733153, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-05 03:01:00.01918+03', '2026-05-05 03:01:00.022197+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 36, 879720, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-06 03:01:00.011218+03', '2026-05-06 03:01:00.01353+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 37, 1027621, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-07 03:01:00.016598+03', '2026-05-07 03:01:00.023712+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 38, 1173719, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-08 03:01:00.014133+03', '2026-05-08 03:01:00.018523+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 39, 1319740, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-09 03:01:00.013333+03', '2026-05-09 03:01:00.015875+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 40, 1465780, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-10 03:01:00.011694+03', '2026-05-10 03:01:00.015796+03');
INSERT INTO cron.job_run_details (jobid, runid, job_pid, database, username, command, status, return_message, start_time, end_time) VALUES (1, 41, 1611789, 'order_database', 'order_admin', '
  UPDATE requests
  SET status = ''review''
  WHERE status = ''open''
    AND deadline_at < now();
  ', 'succeeded', 'UPDATE 0', '2026-05-11 03:01:00.012839+03', '2026-05-11 03:01:00.020403+03');


--
-- Data for Name: admin_event_entity; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_server; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_server_policy; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: associated_policy; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: realm; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm (id, access_code_lifespan, user_action_lifespan, access_token_lifespan, account_theme, admin_theme, email_theme, enabled, events_enabled, events_expiration, login_theme, name, not_before, password_policy, registration_allowed, remember_me, reset_password_allowed, social, ssl_required, sso_idle_timeout, sso_max_lifespan, update_profile_on_soc_login, verify_email, master_admin_client, login_lifespan, internationalization_enabled, default_locale, reg_email_as_username, admin_events_enabled, admin_events_details_enabled, edit_username_allowed, otp_policy_counter, otp_policy_window, otp_policy_period, otp_policy_digits, otp_policy_alg, otp_policy_type, browser_flow, registration_flow, direct_grant_flow, reset_credentials_flow, client_auth_flow, offline_session_idle_timeout, revoke_refresh_token, access_token_life_implicit, login_with_email_allowed, duplicate_emails_allowed, docker_auth_flow, refresh_token_max_reuse, allow_user_managed_access, sso_max_lifespan_remember_me, sso_idle_timeout_remember_me, default_role) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 60, 300, 60, NULL, NULL, NULL, true, false, 0, NULL, 'master', 0, NULL, false, false, false, false, 'EXTERNAL', 1800, 36000, false, false, '23fc1943-a349-4d6e-bf25-888a75ee3d7d', 1800, false, NULL, false, false, false, false, 0, 1, 30, 6, 'HmacSHA1', 'totp', '6d7b91bd-b95d-475e-b7b2-376fa37d1668', '4244b9be-8152-4680-b71d-6fdd2367e0ca', 'cd813f4c-0d0b-4586-b35a-0982405722d7', '456057a4-6ff5-4990-9f38-71db2e9d8e8f', '57cf094b-052e-4eb0-aedf-ee2937a505da', 2592000, false, 900, true, false, '6b642a02-7b8f-4928-8bc1-5f898c3e6899', 0, false, 0, 0, 'f5cec55e-0e1e-4e0e-83c4-5005b0e44017');
INSERT INTO keycloak.realm (id, access_code_lifespan, user_action_lifespan, access_token_lifespan, account_theme, admin_theme, email_theme, enabled, events_enabled, events_expiration, login_theme, name, not_before, password_policy, registration_allowed, remember_me, reset_password_allowed, social, ssl_required, sso_idle_timeout, sso_max_lifespan, update_profile_on_soc_login, verify_email, master_admin_client, login_lifespan, internationalization_enabled, default_locale, reg_email_as_username, admin_events_enabled, admin_events_details_enabled, edit_username_allowed, otp_policy_counter, otp_policy_window, otp_policy_period, otp_policy_digits, otp_policy_alg, otp_policy_type, browser_flow, registration_flow, direct_grant_flow, reset_credentials_flow, client_auth_flow, offline_session_idle_timeout, revoke_refresh_token, access_token_life_implicit, login_with_email_allowed, duplicate_emails_allowed, docker_auth_flow, refresh_token_max_reuse, allow_user_managed_access, sso_max_lifespan_remember_me, sso_idle_timeout_remember_me, default_role) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 300, 1800, 300, NULL, NULL, NULL, true, false, 0, 'acom-offerdesk', 'acom-offerdesk', 1776081758, NULL, true, true, true, false, 'EXTERNAL', 1800, 86400, false, true, '4c572e75-71db-4855-abac-3ae9c6d8f873', 1800, true, 'ru', false, false, false, false, 0, 1, 30, 6, 'HmacSHA1', 'totp', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 'c3df6d97-fd76-4bee-a94f-3c219a87096e', '4c728086-e8dc-47b6-9ea6-ff4d289262ad', '04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', '85701abe-4de8-4fb1-a659-987202ef65f3', 2592000, true, 900, true, false, '95610994-d448-4462-b53f-03d8c1e9c9a4', 0, false, 86400, 1800, '1a9bdb6b-ef2b-4661-8543-62561be47aff');


--
-- Data for Name: authentication_flow; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('6d7b91bd-b95d-475e-b7b2-376fa37d1668', 'browser', 'Browser based authentication', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('d026babe-4538-4121-aae8-f8f24ed28733', 'forms', 'Username, password, otp and other auth forms.', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('866d68f0-14eb-4c07-803f-f3730d5ab783', 'Browser - Conditional 2FA', 'Flow to determine if any 2FA is required for the authentication', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('cd813f4c-0d0b-4586-b35a-0982405722d7', 'direct grant', 'OpenID Connect Resource Owner Grant', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('e8211c7b-de73-4331-94e1-27fdb998f9aa', 'Direct Grant - Conditional OTP', 'Flow to determine if the OTP is required for the authentication', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('4244b9be-8152-4680-b71d-6fdd2367e0ca', 'registration', 'Registration flow', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('7c2b5f98-db1f-4484-850a-6b0e85cc39f9', 'registration form', 'Registration form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'form-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('456057a4-6ff5-4990-9f38-71db2e9d8e8f', 'reset credentials', 'Reset credentials for a user if they forgot their password or something', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('8b0342ef-893a-4f4f-9668-63191c4bdadc', 'Reset - Conditional OTP', 'Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('57cf094b-052e-4eb0-aedf-ee2937a505da', 'clients', 'Base authentication for clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'client-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('ec0d9a43-9b62-48cc-800d-0ddc8eed35d7', 'first broker login', 'Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('435c235b-7113-43ab-bfdb-e24b5bc35aa6', 'User creation or linking', 'Flow for the existing/non-existing user alternatives', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('b8b2bb21-430d-4cf0-bc86-7f176f7c256a', 'Handle Existing Account', 'Handle what to do if there is existing account with same email/username like authenticated identity provider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('4d4ce520-fe9b-4c29-b0e2-9c82bf4ff5be', 'Account verification options', 'Method with which to verify the existing account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('b44ce407-d9c5-40b8-b529-ada3b2d0bfd2', 'Verify Existing Account by Re-authentication', 'Reauthentication of existing account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('9a1448a0-8483-4877-8d28-4c86f52047f0', 'First broker login - Conditional 2FA', 'Flow to determine if any 2FA is required for the authentication', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('c630fcd1-52de-46e6-9de4-bb4b7f659e64', 'saml ecp', 'SAML ECP Profile Authentication Flow', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('6b642a02-7b8f-4928-8bc1-5f898c3e6899', 'docker auth', 'Used by Docker clients to authenticate against the IDP', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 'browser', 'Browser based authentication', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('ae23ef64-9fda-458b-a423-62a33b56e781', 'forms', 'Username, password, otp and other auth forms.', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('b57f66ad-0ef6-4f02-b0df-a0356e762962', 'Browser - Conditional 2FA', 'Flow to determine if any 2FA is required for the authentication', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('5c08eb90-28a8-480c-9423-d657bb24147e', 'Organization', NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('7257a443-866d-4672-af81-2f93de75eec4', 'Browser - Conditional Organization', 'Flow to determine if the organization identity-first login is to be used', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('4c728086-e8dc-47b6-9ea6-ff4d289262ad', 'direct grant', 'OpenID Connect Resource Owner Grant', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('591af6de-874c-4b75-8c70-8d0349915ed0', 'Direct Grant - Conditional OTP', 'Flow to determine if the OTP is required for the authentication', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('c3df6d97-fd76-4bee-a94f-3c219a87096e', 'registration', 'Registration flow', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', 'registration form', 'Registration form', '6b03f9aa-9012-46b3-a691-480d464101db', 'form-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', 'reset credentials', 'Reset credentials for a user if they forgot their password or something', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('2a621573-1a22-4ae7-bcad-87a7b988c3e6', 'Reset - Conditional OTP', 'Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('85701abe-4de8-4fb1-a659-987202ef65f3', 'clients', 'Base authentication for clients', '6b03f9aa-9012-46b3-a691-480d464101db', 'client-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('8d8742ad-d3ce-43ae-a921-2538f1ca162f', 'first broker login', 'Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('3722281a-2672-4a7e-91a1-1e4223db9d71', 'User creation or linking', 'Flow for the existing/non-existing user alternatives', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('62bbd58b-48ac-4d90-9c92-1139348680d0', 'Handle Existing Account', 'Handle what to do if there is existing account with same email/username like authenticated identity provider', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('690dc77c-e3ac-4755-857c-cccebac6e683', 'Account verification options', 'Method with which to verify the existing account', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('764b9d60-6820-4c70-b410-572a9e5e6c57', 'Verify Existing Account by Re-authentication', 'Reauthentication of existing account', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 'First broker login - Conditional 2FA', 'Flow to determine if any 2FA is required for the authentication', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('59981b27-1884-487d-8bf8-da14c5b334c0', 'First Broker Login - Conditional Organization', 'Flow to determine if the authenticator that adds organization members is to be used', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', false, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('ddf389f9-e950-4387-88a8-949ad4190a34', 'saml ecp', 'SAML ECP Profile Authentication Flow', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);
INSERT INTO keycloak.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) VALUES ('95610994-d448-4462-b53f-03d8c1e9c9a4', 'docker auth', 'Used by Docker clients to authenticate against the IDP', '6b03f9aa-9012-46b3-a691-480d464101db', 'basic-flow', true, true);


--
-- Data for Name: authentication_execution; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('1b781e62-8ce3-4010-8357-754fe8ba42a7', NULL, 'auth-cookie', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '6d7b91bd-b95d-475e-b7b2-376fa37d1668', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f2a11eb7-a89c-40a3-8370-759530a56472', NULL, 'auth-spnego', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '6d7b91bd-b95d-475e-b7b2-376fa37d1668', 3, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('320fc61f-59eb-4bfb-ac55-cd2862137423', NULL, 'identity-provider-redirector', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '6d7b91bd-b95d-475e-b7b2-376fa37d1668', 2, 25, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6fcdb062-8c50-4aaf-aac0-db06b268bd3b', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', '6d7b91bd-b95d-475e-b7b2-376fa37d1668', 2, 30, true, 'd026babe-4538-4121-aae8-f8f24ed28733', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('0bd93456-fae9-4eec-80d7-fe5290eb1020', NULL, 'auth-username-password-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'd026babe-4538-4121-aae8-f8f24ed28733', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('e52bfe61-a7d8-4e8a-bd5c-72aff489e7fd', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'd026babe-4538-4121-aae8-f8f24ed28733', 1, 20, true, '866d68f0-14eb-4c07-803f-f3730d5ab783', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('26768ce1-87c6-4b2a-8430-1d3d505cba7a', NULL, 'conditional-user-configured', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '866d68f0-14eb-4c07-803f-f3730d5ab783', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('261b5179-1879-4458-8c8b-6f1055c2be7c', NULL, 'conditional-credential', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '866d68f0-14eb-4c07-803f-f3730d5ab783', 0, 20, false, NULL, '5ebd7d6e-6bf3-4379-9738-a79505ddf0ff');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('304db7de-3bbb-477e-8090-9dd65b34bff4', NULL, 'auth-otp-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '866d68f0-14eb-4c07-803f-f3730d5ab783', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('a1d6e027-0124-48e9-bb52-75eb890135ba', NULL, 'webauthn-authenticator', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '866d68f0-14eb-4c07-803f-f3730d5ab783', 3, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('a681b135-46a8-423b-b62e-ae6611eb4a8b', NULL, 'auth-recovery-authn-code-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '866d68f0-14eb-4c07-803f-f3730d5ab783', 3, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('fe456a1c-605b-4f45-954b-b1e7393335cf', NULL, 'direct-grant-validate-username', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'cd813f4c-0d0b-4586-b35a-0982405722d7', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('010d6006-ccaa-4017-954a-9beac22fb7cb', NULL, 'direct-grant-validate-password', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'cd813f4c-0d0b-4586-b35a-0982405722d7', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('0d03c34c-3bad-4de7-9d63-44c5d431c732', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'cd813f4c-0d0b-4586-b35a-0982405722d7', 1, 30, true, 'e8211c7b-de73-4331-94e1-27fdb998f9aa', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('66abdb15-1a57-4deb-b19e-568631999985', NULL, 'conditional-user-configured', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'e8211c7b-de73-4331-94e1-27fdb998f9aa', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f5f41e30-46c2-4364-8717-c38fed87353d', NULL, 'direct-grant-validate-otp', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'e8211c7b-de73-4331-94e1-27fdb998f9aa', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('c975558a-4b60-4891-8c97-59a3a0c6a967', NULL, 'registration-page-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4244b9be-8152-4680-b71d-6fdd2367e0ca', 0, 10, true, '7c2b5f98-db1f-4484-850a-6b0e85cc39f9', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('8522c41e-0e10-4b0d-8ab9-a634a2d88686', NULL, 'registration-user-creation', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '7c2b5f98-db1f-4484-850a-6b0e85cc39f9', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('e5766376-10e6-4366-aa7b-765c023c0621', NULL, 'registration-password-action', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '7c2b5f98-db1f-4484-850a-6b0e85cc39f9', 0, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6263e615-06de-49d5-ae21-7b86e122fd37', NULL, 'registration-recaptcha-action', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '7c2b5f98-db1f-4484-850a-6b0e85cc39f9', 3, 60, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('53296fdb-e15a-4ee5-b1ec-fd5619e7eb23', NULL, 'registration-terms-and-conditions', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '7c2b5f98-db1f-4484-850a-6b0e85cc39f9', 3, 70, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('112fd7b9-d861-4079-91c7-0e1bf3c8832b', NULL, 'reset-credentials-choose-user', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '456057a4-6ff5-4990-9f38-71db2e9d8e8f', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f52043c0-cbe5-440b-879c-6ff1bd7b24b1', NULL, 'reset-credential-email', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '456057a4-6ff5-4990-9f38-71db2e9d8e8f', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('cc9c6fef-d01a-40bf-a3a3-a9dfeb862d3f', NULL, 'reset-password', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '456057a4-6ff5-4990-9f38-71db2e9d8e8f', 0, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f8975295-b63b-4f66-a3a9-440c3e95eee9', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', '456057a4-6ff5-4990-9f38-71db2e9d8e8f', 1, 40, true, '8b0342ef-893a-4f4f-9668-63191c4bdadc', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('ebf6d40f-d334-41a4-8bdf-0fd2229d05ed', NULL, 'conditional-user-configured', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '8b0342ef-893a-4f4f-9668-63191c4bdadc', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('80fdf79a-1599-49a9-b7df-aa0e523f0b95', NULL, 'reset-otp', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '8b0342ef-893a-4f4f-9668-63191c4bdadc', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('a4d87496-2355-4c41-a59b-8c542e8c4b0f', NULL, 'client-secret', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '57cf094b-052e-4eb0-aedf-ee2937a505da', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('c860dc91-6dc5-4512-ad5b-c89ca2139427', NULL, 'client-jwt', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '57cf094b-052e-4eb0-aedf-ee2937a505da', 2, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('2cefa188-d191-41aa-9392-fbb82c8a2579', NULL, 'client-secret-jwt', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '57cf094b-052e-4eb0-aedf-ee2937a505da', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('9223f873-5800-4c29-adb1-22cf3e96ed3e', NULL, 'client-x509', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '57cf094b-052e-4eb0-aedf-ee2937a505da', 2, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('0fad040f-c4fe-428e-90a7-d02472656c04', NULL, 'idp-review-profile', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'ec0d9a43-9b62-48cc-800d-0ddc8eed35d7', 0, 10, false, NULL, '031f4704-87ed-4472-9b5e-84b05720f5e1');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('8a5a9299-adf5-45f1-ba1e-456f8bd58771', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'ec0d9a43-9b62-48cc-800d-0ddc8eed35d7', 0, 20, true, '435c235b-7113-43ab-bfdb-e24b5bc35aa6', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('110b275d-1d2f-4376-b648-b79c9bbae512', NULL, 'idp-create-user-if-unique', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '435c235b-7113-43ab-bfdb-e24b5bc35aa6', 2, 10, false, NULL, 'e902e2fd-ef55-438f-b96c-f74a7dbab420');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('98e24bc4-c904-4737-b134-27fcaaca4cb2', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', '435c235b-7113-43ab-bfdb-e24b5bc35aa6', 2, 20, true, 'b8b2bb21-430d-4cf0-bc86-7f176f7c256a', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('75de5113-c90e-48b7-8454-942871366b5a', NULL, 'idp-confirm-link', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'b8b2bb21-430d-4cf0-bc86-7f176f7c256a', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('361fe6f8-ecdf-4817-93a4-b6d504fbd37e', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'b8b2bb21-430d-4cf0-bc86-7f176f7c256a', 0, 20, true, '4d4ce520-fe9b-4c29-b0e2-9c82bf4ff5be', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('23bcd1f0-40c7-4386-b126-48fedcec2c1b', NULL, 'idp-email-verification', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4d4ce520-fe9b-4c29-b0e2-9c82bf4ff5be', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('41119f90-b788-4b2f-802c-5e93e3cad2a5', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4d4ce520-fe9b-4c29-b0e2-9c82bf4ff5be', 2, 20, true, 'b44ce407-d9c5-40b8-b529-ada3b2d0bfd2', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6cbc5bf1-aa5b-4d34-a6ab-8918bc54cf71', NULL, 'idp-username-password-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'b44ce407-d9c5-40b8-b529-ada3b2d0bfd2', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('038a7b2a-77f0-46a3-b44d-ee52d9f9127c', NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'b44ce407-d9c5-40b8-b529-ada3b2d0bfd2', 1, 20, true, '9a1448a0-8483-4877-8d28-4c86f52047f0', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('725f5d15-4bec-40ae-952b-883eaddd5ecb', NULL, 'conditional-user-configured', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '9a1448a0-8483-4877-8d28-4c86f52047f0', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('057341bb-05ed-4c94-91dd-67a738242674', NULL, 'conditional-credential', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '9a1448a0-8483-4877-8d28-4c86f52047f0', 0, 20, false, NULL, 'ec4ed13c-53c8-4a97-89fe-f9ed19e7c1ac');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('815bf22c-355e-4b0b-afbc-41f149611afa', NULL, 'auth-otp-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '9a1448a0-8483-4877-8d28-4c86f52047f0', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('2cb5e17c-8c32-429f-ba16-ee29c224eaee', NULL, 'webauthn-authenticator', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '9a1448a0-8483-4877-8d28-4c86f52047f0', 3, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('b3a946e8-0461-4f73-b2ff-189553a3bd62', NULL, 'auth-recovery-authn-code-form', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '9a1448a0-8483-4877-8d28-4c86f52047f0', 3, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('24fde06d-c6eb-4d4b-954d-13a153e9b22a', NULL, 'http-basic-authenticator', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'c630fcd1-52de-46e6-9de4-bb4b7f659e64', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('7eef509c-b29c-4459-840e-e1b7614259c5', NULL, 'docker-http-basic-authenticator', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '6b642a02-7b8f-4928-8bc1-5f898c3e6899', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('fdf3ded8-a4d9-4b54-8e29-c3e173a02909', NULL, 'auth-cookie', '6b03f9aa-9012-46b3-a691-480d464101db', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('93ac698a-94a7-4092-8627-e783a5aea57c', NULL, 'auth-spnego', '6b03f9aa-9012-46b3-a691-480d464101db', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 3, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('3d874e77-6f1e-409a-82da-a711ca72d9c5', NULL, 'identity-provider-redirector', '6b03f9aa-9012-46b3-a691-480d464101db', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 2, 25, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('9793b028-50ad-4fee-8838-ee7fd695b28c', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 2, 30, true, 'ae23ef64-9fda-458b-a423-62a33b56e781', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('e235aeec-0d7c-45ee-8158-40ef13df0ca5', NULL, 'auth-username-password-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'ae23ef64-9fda-458b-a423-62a33b56e781', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('b0a0a976-e617-4b78-9c1d-8a4b90384207', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'ae23ef64-9fda-458b-a423-62a33b56e781', 1, 20, true, 'b57f66ad-0ef6-4f02-b0df-a0356e762962', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('81fc66f3-b5cb-4895-8643-00791c60d8af', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', 'b57f66ad-0ef6-4f02-b0df-a0356e762962', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('8d7c061a-8856-401c-a05b-ec95b5bcb1b1', NULL, 'conditional-credential', '6b03f9aa-9012-46b3-a691-480d464101db', 'b57f66ad-0ef6-4f02-b0df-a0356e762962', 0, 20, false, NULL, '1a801bd6-4e58-4ac2-bbfd-30a0dc9f6afc');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('1c22b325-02f1-45f1-819e-ed0241fa2f75', NULL, 'auth-otp-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'b57f66ad-0ef6-4f02-b0df-a0356e762962', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('71496560-86e0-4a34-8151-52dcf1547c30', NULL, 'webauthn-authenticator', '6b03f9aa-9012-46b3-a691-480d464101db', 'b57f66ad-0ef6-4f02-b0df-a0356e762962', 3, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('0586e1cd-cdbd-40b4-aa8f-dd9b894116ca', NULL, 'auth-recovery-authn-code-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'b57f66ad-0ef6-4f02-b0df-a0356e762962', 3, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('cf583938-b578-4608-82f4-0ff71ab176b7', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'f12d30e1-aa9f-4771-bfad-b5ce99027ff1', 2, 26, true, '5c08eb90-28a8-480c-9423-d657bb24147e', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('4d5daea9-98f1-4207-9157-aae03fae6404', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '5c08eb90-28a8-480c-9423-d657bb24147e', 1, 10, true, '7257a443-866d-4672-af81-2f93de75eec4', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6e040cb4-e2a1-4b88-93f1-5ebcf07acdff', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', '7257a443-866d-4672-af81-2f93de75eec4', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f1a07d49-660b-46c8-b58b-9ad43f8c46fb', NULL, 'organization', '6b03f9aa-9012-46b3-a691-480d464101db', '7257a443-866d-4672-af81-2f93de75eec4', 2, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('26d84792-5dc9-4d77-8b0d-e5bbe61b11bc', NULL, 'direct-grant-validate-username', '6b03f9aa-9012-46b3-a691-480d464101db', '4c728086-e8dc-47b6-9ea6-ff4d289262ad', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('7a975cf9-c4ad-4642-86d0-e98c49f5603b', NULL, 'direct-grant-validate-password', '6b03f9aa-9012-46b3-a691-480d464101db', '4c728086-e8dc-47b6-9ea6-ff4d289262ad', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('bb7d8afe-400b-478b-b880-09da3e5dce08', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '4c728086-e8dc-47b6-9ea6-ff4d289262ad', 1, 30, true, '591af6de-874c-4b75-8c70-8d0349915ed0', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('d0f2c06f-fda8-4f85-a74c-2bda14b87334', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', '591af6de-874c-4b75-8c70-8d0349915ed0', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('9ae63859-666a-4c23-b44a-b2fc6ccfdc98', NULL, 'direct-grant-validate-otp', '6b03f9aa-9012-46b3-a691-480d464101db', '591af6de-874c-4b75-8c70-8d0349915ed0', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('23972212-beb0-444b-b20b-c1791eee4a20', NULL, 'registration-page-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'c3df6d97-fd76-4bee-a94f-3c219a87096e', 0, 10, true, '0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6e05c589-520b-492a-b54d-bc05c4610eb2', NULL, 'registration-user-creation', '6b03f9aa-9012-46b3-a691-480d464101db', '0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('bc96a28c-624c-44cb-91a6-0a57290b8c5c', NULL, 'registration-password-action', '6b03f9aa-9012-46b3-a691-480d464101db', '0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', 0, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('308c99fe-db96-40c7-a842-73edc337eb4a', NULL, 'registration-recaptcha-action', '6b03f9aa-9012-46b3-a691-480d464101db', '0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', 3, 60, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('af80ca90-bcba-47ed-a296-54ec2ba1c43d', NULL, 'registration-terms-and-conditions', '6b03f9aa-9012-46b3-a691-480d464101db', '0ab4cf95-de1f-4ff8-a217-41ca7d2193b5', 3, 70, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('b8296457-d241-4b41-8139-843e200b52e6', NULL, 'reset-credentials-choose-user', '6b03f9aa-9012-46b3-a691-480d464101db', '04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('42dc72ac-282f-48c1-8447-b965864da3b9', NULL, 'reset-credential-email', '6b03f9aa-9012-46b3-a691-480d464101db', '04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('6abfb6ba-2c09-49ef-9bfe-7dd496ecf044', NULL, 'reset-password', '6b03f9aa-9012-46b3-a691-480d464101db', '04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', 0, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('65c5dc86-3556-4fa0-b3b4-77402d2bfd42', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '04d76edd-80f9-4b3d-9a2a-0fb1ea20eccc', 1, 40, true, '2a621573-1a22-4ae7-bcad-87a7b988c3e6', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('9d882e55-4b4b-434f-b5e8-93ab2bde3465', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', '2a621573-1a22-4ae7-bcad-87a7b988c3e6', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('193bd596-b46d-4504-ad90-2064b2fd10f8', NULL, 'reset-otp', '6b03f9aa-9012-46b3-a691-480d464101db', '2a621573-1a22-4ae7-bcad-87a7b988c3e6', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('3411bb16-3198-4c96-8715-e794d5c793f6', NULL, 'client-secret', '6b03f9aa-9012-46b3-a691-480d464101db', '85701abe-4de8-4fb1-a659-987202ef65f3', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('32231eca-bd8a-4ad6-ae04-2afab2b4db43', NULL, 'client-jwt', '6b03f9aa-9012-46b3-a691-480d464101db', '85701abe-4de8-4fb1-a659-987202ef65f3', 2, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('7ad35577-6aa6-4b88-b489-e5599edb6d57', NULL, 'client-secret-jwt', '6b03f9aa-9012-46b3-a691-480d464101db', '85701abe-4de8-4fb1-a659-987202ef65f3', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('033665c3-317f-4dff-848c-c644649080f7', NULL, 'client-x509', '6b03f9aa-9012-46b3-a691-480d464101db', '85701abe-4de8-4fb1-a659-987202ef65f3', 2, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('9e092aaf-fa0c-4a38-bfcf-c30d746f3e23', NULL, 'idp-review-profile', '6b03f9aa-9012-46b3-a691-480d464101db', '8d8742ad-d3ce-43ae-a921-2538f1ca162f', 0, 10, false, NULL, 'ea8a2d1d-7860-485d-a431-d017e1103e6c');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('3e22338d-7eec-4aca-ac40-7193177a9892', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '8d8742ad-d3ce-43ae-a921-2538f1ca162f', 0, 20, true, '3722281a-2672-4a7e-91a1-1e4223db9d71', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('5679ef4f-e770-4d7a-84ab-e5e05fe95bd9', NULL, 'idp-create-user-if-unique', '6b03f9aa-9012-46b3-a691-480d464101db', '3722281a-2672-4a7e-91a1-1e4223db9d71', 2, 10, false, NULL, '6eeccf7f-5132-4bea-bfdb-c83a899af0d9');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('c73cdd26-cdc5-4ec9-a761-16e442b72aa1', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '3722281a-2672-4a7e-91a1-1e4223db9d71', 2, 20, true, '62bbd58b-48ac-4d90-9c92-1139348680d0', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('3ba0eda4-f272-4afa-ac26-1fd9d62cc698', NULL, 'idp-confirm-link', '6b03f9aa-9012-46b3-a691-480d464101db', '62bbd58b-48ac-4d90-9c92-1139348680d0', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('b1ea4a13-ae37-4f6e-a98f-4b9b8d4e14ef', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '62bbd58b-48ac-4d90-9c92-1139348680d0', 0, 20, true, '690dc77c-e3ac-4755-857c-cccebac6e683', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('bfb3a27f-f94f-4102-a2e4-91d08526eee7', NULL, 'idp-email-verification', '6b03f9aa-9012-46b3-a691-480d464101db', '690dc77c-e3ac-4755-857c-cccebac6e683', 2, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('48c0ee66-67bc-4cad-b7be-ccfd2a3b5788', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '690dc77c-e3ac-4755-857c-cccebac6e683', 2, 20, true, '764b9d60-6820-4c70-b410-572a9e5e6c57', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('e890150f-905d-4e81-a6ea-b457ec1a9397', NULL, 'idp-username-password-form', '6b03f9aa-9012-46b3-a691-480d464101db', '764b9d60-6820-4c70-b410-572a9e5e6c57', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f72673ee-b47a-427d-b1e8-6c6e103ac621', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '764b9d60-6820-4c70-b410-572a9e5e6c57', 1, 20, true, 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('41e2a218-aa34-4308-8d5e-0e0c083a4e57', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('d278ff24-fdda-4c7c-9fe5-9e5fcec2adb1', NULL, 'conditional-credential', '6b03f9aa-9012-46b3-a691-480d464101db', 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 0, 20, false, NULL, 'cdd8f4fb-c993-44e2-89d4-fa59054ff2d5');
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('4678f8dd-522f-4865-ab00-0040452c017d', NULL, 'auth-otp-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 2, 30, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('5c6b6def-4acc-4767-ac7f-49a7135c9906', NULL, 'webauthn-authenticator', '6b03f9aa-9012-46b3-a691-480d464101db', 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 3, 40, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('960164f5-a4ea-4594-87cd-5066e1ea0093', NULL, 'auth-recovery-authn-code-form', '6b03f9aa-9012-46b3-a691-480d464101db', 'dadcb8bc-7385-4310-8ca3-481b0ce27d5c', 3, 50, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('135fa5cd-8b3d-41d8-85b7-04469bc8f049', NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', '8d8742ad-d3ce-43ae-a921-2538f1ca162f', 1, 60, true, '59981b27-1884-487d-8bf8-da14c5b334c0', NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('b3d52a6a-918b-410a-ba62-2a5c12425282', NULL, 'conditional-user-configured', '6b03f9aa-9012-46b3-a691-480d464101db', '59981b27-1884-487d-8bf8-da14c5b334c0', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('1af9a170-7790-4a6a-a3a1-80eb2511379b', NULL, 'idp-add-organization-member', '6b03f9aa-9012-46b3-a691-480d464101db', '59981b27-1884-487d-8bf8-da14c5b334c0', 0, 20, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('13b9807e-4b6c-4413-a81d-70ab35a2d0b9', NULL, 'http-basic-authenticator', '6b03f9aa-9012-46b3-a691-480d464101db', 'ddf389f9-e950-4387-88a8-949ad4190a34', 0, 10, false, NULL, NULL);
INSERT INTO keycloak.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) VALUES ('f2885578-e3c0-473a-aef9-ff2e095b99bf', NULL, 'docker-http-basic-authenticator', '6b03f9aa-9012-46b3-a691-480d464101db', '95610994-d448-4462-b53f-03d8c1e9c9a4', 0, 10, false, NULL, NULL);


--
-- Data for Name: authenticator_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('5ebd7d6e-6bf3-4379-9738-a79505ddf0ff', 'browser-conditional-credential', '273f6fe8-dc27-45b7-815b-a759a2722e8f');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('031f4704-87ed-4472-9b5e-84b05720f5e1', 'review profile config', '273f6fe8-dc27-45b7-815b-a759a2722e8f');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('e902e2fd-ef55-438f-b96c-f74a7dbab420', 'create unique user config', '273f6fe8-dc27-45b7-815b-a759a2722e8f');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('ec4ed13c-53c8-4a97-89fe-f9ed19e7c1ac', 'first-broker-login-conditional-credential', '273f6fe8-dc27-45b7-815b-a759a2722e8f');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('1a801bd6-4e58-4ac2-bbfd-30a0dc9f6afc', 'browser-conditional-credential', '6b03f9aa-9012-46b3-a691-480d464101db');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('ea8a2d1d-7860-485d-a431-d017e1103e6c', 'review profile config', '6b03f9aa-9012-46b3-a691-480d464101db');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('6eeccf7f-5132-4bea-bfdb-c83a899af0d9', 'create unique user config', '6b03f9aa-9012-46b3-a691-480d464101db');
INSERT INTO keycloak.authenticator_config (id, alias, realm_id) VALUES ('cdd8f4fb-c993-44e2-89d4-fa59054ff2d5', 'first-broker-login-conditional-credential', '6b03f9aa-9012-46b3-a691-480d464101db');


--
-- Data for Name: authenticator_config_entry; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('031f4704-87ed-4472-9b5e-84b05720f5e1', 'missing', 'update.profile.on.first.login');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('5ebd7d6e-6bf3-4379-9738-a79505ddf0ff', 'webauthn-passwordless', 'credentials');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('e902e2fd-ef55-438f-b96c-f74a7dbab420', 'false', 'require.password.update.after.registration');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('ec4ed13c-53c8-4a97-89fe-f9ed19e7c1ac', 'webauthn-passwordless', 'credentials');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('1a801bd6-4e58-4ac2-bbfd-30a0dc9f6afc', 'webauthn-passwordless', 'credentials');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('6eeccf7f-5132-4bea-bfdb-c83a899af0d9', 'false', 'require.password.update.after.registration');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('cdd8f4fb-c993-44e2-89d4-fa59054ff2d5', 'webauthn-passwordless', 'credentials');
INSERT INTO keycloak.authenticator_config_entry (authenticator_id, value, name) VALUES ('ea8a2d1d-7860-485d-a431-d017e1103e6c', 'missing', 'update.profile.on.first.login');


--
-- Data for Name: broker_link; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: client; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, false, 'master-realm', 0, false, NULL, NULL, true, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, 0, false, false, 'master Realm', false, 'client-secret', NULL, NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', true, false, 'account', 0, true, NULL, '/realms/master/account/', false, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'openid-connect', 0, false, false, '${client_account}', false, 'client-secret', '${authBaseUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', true, false, 'account-console', 0, true, NULL, '/realms/master/account/', false, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'openid-connect', 0, false, false, '${client_account-console}', false, 'client-secret', '${authBaseUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', true, false, 'broker', 0, false, NULL, NULL, true, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'openid-connect', 0, false, false, '${client_broker}', false, 'client-secret', NULL, NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', true, true, 'security-admin-console', 0, true, NULL, '/admin/master/console/', false, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'openid-connect', 0, false, false, '${client_security-admin-console}', false, 'client-secret', '${authAdminUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', true, true, 'admin-cli', 0, true, NULL, NULL, false, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'openid-connect', 0, false, false, '${client_admin-cli}', false, 'client-secret', NULL, NULL, NULL, false, false, true, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('4c572e75-71db-4855-abac-3ae9c6d8f873', true, false, 'acom-offerdesk-realm', 0, false, NULL, NULL, true, NULL, false, '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, 0, false, false, 'acom-offerdesk Realm', false, 'client-secret', NULL, NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, false, 'realm-management', 0, false, NULL, NULL, true, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_realm-management}', false, 'client-secret', NULL, NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', true, false, 'account', 0, true, NULL, '/realms/acom-offerdesk/account/', false, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_account}', false, 'client-secret', '${authBaseUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', true, false, 'account-console', 0, true, NULL, '/realms/acom-offerdesk/account/', false, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_account-console}', false, 'client-secret', '${authBaseUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', true, false, 'broker', 0, false, NULL, NULL, true, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_broker}', false, 'client-secret', NULL, NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', true, true, 'security-admin-console', 0, true, NULL, '/admin/acom-offerdesk/console/', false, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_security-admin-console}', false, 'client-secret', '${authAdminUrl}', NULL, NULL, true, false, false, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', true, true, 'admin-cli', 0, true, NULL, NULL, false, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', 0, false, false, '${client_admin-cli}', false, 'client-secret', NULL, NULL, NULL, false, false, true, false);
INSERT INTO keycloak.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', true, true, 'acom-offerdesk-web', 0, true, NULL, 'https://app.acom-offer-desk.ru', false, NULL, false, '6b03f9aa-9012-46b3-a691-480d464101db', 'openid-connect', -1, false, false, 'AcomOfferDesk Web', false, 'client-secret', 'https://app.acom-offer-desk.ru', NULL, NULL, true, false, false, false);


--
-- Data for Name: client_attributes; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'pkce.code.challenge.method', 'S256');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'pkce.code.challenge.method', 'S256');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'client.use.lightweight.access.token.enabled', 'true');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'client.use.lightweight.access.token.enabled', 'true');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', 'pkce.code.challenge.method', 'S256');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', 'post.logout.redirect.uris', '+');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', 'pkce.code.challenge.method', 'S256');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', 'client.use.lightweight.access.token.enabled', 'true');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', 'client.use.lightweight.access.token.enabled', 'true');
INSERT INTO keycloak.client_attributes (client_id, name, value) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', 'realm_client', 'false');


--
-- Data for Name: client_auth_flow_bindings; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: client_initial_access; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: client_node_registrations; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: client_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('edd03863-01ef-4156-8b0b-0cbd87959c4d', 'offline_access', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect built-in scope: offline_access', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('68017d7b-7c27-4bc6-8346-348fc25f92d2', 'role_list', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'SAML role list', 'saml');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('620a3cd4-2f16-43f8-8c86-8123af3f410d', 'saml_organization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'Organization Membership', 'saml');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('07effd1e-fb39-4217-8cd0-bd8744c37376', 'profile', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect built-in scope: profile', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('da0c0f2d-cf22-4514-ad78-1e3864a5d873', 'email', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect built-in scope: email', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('87094c14-6111-47ee-8bea-6f77339383cf', 'address', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect built-in scope: address', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('404593df-a9d2-47e7-a7b4-b5549cfdf9f5', 'phone', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect built-in scope: phone', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('9014bdd1-1091-452c-9c01-58d05f8002af', 'roles', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect scope for add user roles to the access token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', 'web-origins', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect scope for add allowed web origins to the access token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', 'microprofile-jwt', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'Microprofile - JWT built-in scope', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('a9740ed8-189f-4138-82df-5f4b05994d5e', 'acr', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect scope for add acr (authentication context class reference) to the token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('7b79221b-2aef-4b37-bb4b-d0b93032facf', 'basic', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'OpenID Connect scope for add all basic claims to the token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('8abf3b84-3370-4855-a511-3c3c32d2743f', 'service_account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'Specific scope for a client enabled for service accounts', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', 'organization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'Additional claims about the organization a subject belongs to', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('09b540d4-e59e-42bb-a28d-ef6381c94dac', 'offline_access', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect built-in scope: offline_access', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('1db071da-7320-4393-b435-ac8d8041e7b0', 'role_list', '6b03f9aa-9012-46b3-a691-480d464101db', 'SAML role list', 'saml');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('688eff0e-5e56-492a-9503-8644d6e8c4c2', 'saml_organization', '6b03f9aa-9012-46b3-a691-480d464101db', 'Organization Membership', 'saml');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('05f865b2-1093-4731-b3d0-c07daa54ca11', 'profile', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect built-in scope: profile', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('158e3a24-8cb8-49f5-8631-0fbb4e8daf82', 'email', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect built-in scope: email', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('50a80748-2a11-4841-9e9e-5ec88b78aaad', 'address', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect built-in scope: address', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('54bab3f8-b662-4249-b82c-7f01f7237124', 'phone', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect built-in scope: phone', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('75cbc876-53fd-422e-b104-b5d420e71dd6', 'roles', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect scope for add user roles to the access token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('ceb5a1ef-c8f8-4461-9c45-4062ac058424', 'web-origins', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect scope for add allowed web origins to the access token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('6fd65251-100b-4201-951c-037b8e658177', 'microprofile-jwt', '6b03f9aa-9012-46b3-a691-480d464101db', 'Microprofile - JWT built-in scope', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', 'acr', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect scope for add acr (authentication context class reference) to the token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('c1da6476-297c-4a19-b6ae-9c3889533aa9', 'basic', '6b03f9aa-9012-46b3-a691-480d464101db', 'OpenID Connect scope for add all basic claims to the token', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('632ace5c-68c7-49dc-9833-f81bd49649b9', 'service_account', '6b03f9aa-9012-46b3-a691-480d464101db', 'Specific scope for a client enabled for service accounts', 'openid-connect');
INSERT INTO keycloak.client_scope (id, name, realm_id, description, protocol) VALUES ('43494a79-3bc5-4c7b-b7e5-8c67caf31365', 'organization', '6b03f9aa-9012-46b3-a691-480d464101db', 'Additional claims about the organization a subject belongs to', 'openid-connect');


--
-- Data for Name: client_scope_attributes; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('edd03863-01ef-4156-8b0b-0cbd87959c4d', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('edd03863-01ef-4156-8b0b-0cbd87959c4d', '${offlineAccessScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('68017d7b-7c27-4bc6-8346-348fc25f92d2', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('68017d7b-7c27-4bc6-8346-348fc25f92d2', '${samlRoleListScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('620a3cd4-2f16-43f8-8c86-8123af3f410d', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('07effd1e-fb39-4217-8cd0-bd8744c37376', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('07effd1e-fb39-4217-8cd0-bd8744c37376', '${profileScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('07effd1e-fb39-4217-8cd0-bd8744c37376', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('da0c0f2d-cf22-4514-ad78-1e3864a5d873', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('da0c0f2d-cf22-4514-ad78-1e3864a5d873', '${emailScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('da0c0f2d-cf22-4514-ad78-1e3864a5d873', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('87094c14-6111-47ee-8bea-6f77339383cf', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('87094c14-6111-47ee-8bea-6f77339383cf', '${addressScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('87094c14-6111-47ee-8bea-6f77339383cf', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('404593df-a9d2-47e7-a7b4-b5549cfdf9f5', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('404593df-a9d2-47e7-a7b4-b5549cfdf9f5', '${phoneScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('404593df-a9d2-47e7-a7b4-b5549cfdf9f5', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('9014bdd1-1091-452c-9c01-58d05f8002af', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('9014bdd1-1091-452c-9c01-58d05f8002af', '${rolesScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('9014bdd1-1091-452c-9c01-58d05f8002af', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', '', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('a9740ed8-189f-4138-82df-5f4b05994d5e', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('a9740ed8-189f-4138-82df-5f4b05994d5e', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('7b79221b-2aef-4b37-bb4b-d0b93032facf', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('7b79221b-2aef-4b37-bb4b-d0b93032facf', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('8abf3b84-3370-4855-a511-3c3c32d2743f', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('8abf3b84-3370-4855-a511-3c3c32d2743f', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', '${organizationScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('09b540d4-e59e-42bb-a28d-ef6381c94dac', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('09b540d4-e59e-42bb-a28d-ef6381c94dac', '${offlineAccessScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('1db071da-7320-4393-b435-ac8d8041e7b0', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('1db071da-7320-4393-b435-ac8d8041e7b0', '${samlRoleListScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('688eff0e-5e56-492a-9503-8644d6e8c4c2', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('05f865b2-1093-4731-b3d0-c07daa54ca11', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('05f865b2-1093-4731-b3d0-c07daa54ca11', '${profileScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('05f865b2-1093-4731-b3d0-c07daa54ca11', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('158e3a24-8cb8-49f5-8631-0fbb4e8daf82', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('158e3a24-8cb8-49f5-8631-0fbb4e8daf82', '${emailScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('158e3a24-8cb8-49f5-8631-0fbb4e8daf82', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('50a80748-2a11-4841-9e9e-5ec88b78aaad', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('50a80748-2a11-4841-9e9e-5ec88b78aaad', '${addressScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('50a80748-2a11-4841-9e9e-5ec88b78aaad', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('54bab3f8-b662-4249-b82c-7f01f7237124', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('54bab3f8-b662-4249-b82c-7f01f7237124', '${phoneScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('54bab3f8-b662-4249-b82c-7f01f7237124', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('75cbc876-53fd-422e-b104-b5d420e71dd6', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('75cbc876-53fd-422e-b104-b5d420e71dd6', '${rolesScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('75cbc876-53fd-422e-b104-b5d420e71dd6', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('ceb5a1ef-c8f8-4461-9c45-4062ac058424', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('ceb5a1ef-c8f8-4461-9c45-4062ac058424', '', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('ceb5a1ef-c8f8-4461-9c45-4062ac058424', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('6fd65251-100b-4201-951c-037b8e658177', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('6fd65251-100b-4201-951c-037b8e658177', 'true', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('c1da6476-297c-4a19-b6ae-9c3889533aa9', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('c1da6476-297c-4a19-b6ae-9c3889533aa9', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('632ace5c-68c7-49dc-9833-f81bd49649b9', 'false', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('632ace5c-68c7-49dc-9833-f81bd49649b9', 'false', 'include.in.token.scope');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('43494a79-3bc5-4c7b-b7e5-8c67caf31365', 'true', 'display.on.consent.screen');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('43494a79-3bc5-4c7b-b7e5-8c67caf31365', '${organizationScopeConsentText}', 'consent.screen.text');
INSERT INTO keycloak.client_scope_attributes (scope_id, value, name) VALUES ('43494a79-3bc5-4c7b-b7e5-8c67caf31365', 'true', 'include.in.token.scope');


--
-- Data for Name: client_scope_client; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('aa678413-b137-42ed-9dde-703b126d7d5f', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('8cab183a-28a5-4d7d-bc0c-098b0525f089', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('23fc1943-a349-4d6e-bf25-888a75ee3d7d', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('bcb5af9b-2a0a-4175-96a9-ecad91bd5bd7', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ca6be0ae-5a10-46db-8217-aff854173617', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('44cb6ea7-95da-4e10-8b67-0f6cd9558a58', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.client_scope_client (client_id, scope_id, default_scope) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);


--
-- Data for Name: client_scope_role_mapping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.client_scope_role_mapping (scope_id, role_id) VALUES ('edd03863-01ef-4156-8b0b-0cbd87959c4d', '6f50235d-13da-4f67-89b6-2efd74cb80af');
INSERT INTO keycloak.client_scope_role_mapping (scope_id, role_id) VALUES ('09b540d4-e59e-42bb-a28d-ef6381c94dac', 'dc258724-34b8-4804-a513-50f2aa6ca988');


--
-- Data for Name: component; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('97a85410-f644-4c5a-8a29-f5b0ee02da35', 'Trusted Hosts', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'trusted-hosts', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('4f5c59f9-9ae5-48de-b7d3-14e7395140b4', 'Consent Required', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'consent-required', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('bbfc5875-6232-4d16-ac09-51bc3a96f5e7', 'Full Scope Disabled', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'scope', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('04400156-9f11-4656-a136-1266eb39e172', 'Max Clients Limit', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'max-clients', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('187808b3-be8d-4cc0-a59c-e65a0c46087e', 'Allowed Protocol Mapper Types', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'allowed-protocol-mappers', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('8b2c49c1-8d44-4ecf-858e-ee951b229d9e', 'Allowed Client Scopes', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'allowed-client-templates', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('8e92d599-ae54-4914-9164-810749c06d3b', 'Allowed Registration Web Origins', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'registration-web-origins', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'Allowed Protocol Mapper Types', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'allowed-protocol-mappers', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'authenticated');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('f3000c00-1a53-4502-8dc6-6dfb56a4bff2', 'Allowed Client Scopes', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'allowed-client-templates', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'authenticated');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('7ec342bc-1922-4c9f-8130-deb2c55c27b6', 'Allowed Registration Web Origins', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'registration-web-origins', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'authenticated');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('e75c9aee-9922-4aa8-9a36-d44ee19828e8', 'rsa-generated', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'rsa-generated', 'org.keycloak.keys.KeyProvider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('2a68f012-806b-4374-9e29-41296c866760', 'rsa-enc-generated', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'rsa-enc-generated', 'org.keycloak.keys.KeyProvider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('9b481e32-d147-45fd-b626-1541c191e4ea', 'hmac-generated-hs512', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'hmac-generated', 'org.keycloak.keys.KeyProvider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('095f8189-21fd-40e1-821c-85567dd9e4e4', 'aes-generated', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'aes-generated', 'org.keycloak.keys.KeyProvider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('cba1c6e5-7ea1-4a34-86b1-214bab417444', NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'declarative-user-profile', 'org.keycloak.userprofile.UserProfileProvider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('7d007295-df3f-4c29-b261-49f3f3b8db45', 'rsa-generated', '6b03f9aa-9012-46b3-a691-480d464101db', 'rsa-generated', 'org.keycloak.keys.KeyProvider', '6b03f9aa-9012-46b3-a691-480d464101db', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('065581b9-9f09-4f08-936d-109ead0aa12c', 'rsa-enc-generated', '6b03f9aa-9012-46b3-a691-480d464101db', 'rsa-enc-generated', 'org.keycloak.keys.KeyProvider', '6b03f9aa-9012-46b3-a691-480d464101db', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('51695a6e-fb22-4cb4-9d26-c6c0e781c1b1', 'hmac-generated-hs512', '6b03f9aa-9012-46b3-a691-480d464101db', 'hmac-generated', 'org.keycloak.keys.KeyProvider', '6b03f9aa-9012-46b3-a691-480d464101db', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('5a0de682-35b7-4393-bbf0-f8060dfa96c5', 'aes-generated', '6b03f9aa-9012-46b3-a691-480d464101db', 'aes-generated', 'org.keycloak.keys.KeyProvider', '6b03f9aa-9012-46b3-a691-480d464101db', NULL);
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('ad114bf2-9f8b-4435-8d57-23d9f959096d', 'Trusted Hosts', '6b03f9aa-9012-46b3-a691-480d464101db', 'trusted-hosts', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('b2997649-a2cc-4184-a375-84a815d7ccbb', 'Consent Required', '6b03f9aa-9012-46b3-a691-480d464101db', 'consent-required', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('bc357ad6-fb54-4e07-867a-cc8929590990', 'Full Scope Disabled', '6b03f9aa-9012-46b3-a691-480d464101db', 'scope', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('4d2c521f-c1bf-4d59-bc61-5ba801793421', 'Max Clients Limit', '6b03f9aa-9012-46b3-a691-480d464101db', 'max-clients', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('157edc3d-16af-4384-89e6-22091a452c48', 'Allowed Protocol Mapper Types', '6b03f9aa-9012-46b3-a691-480d464101db', 'allowed-protocol-mappers', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('00b0f07e-270e-41d4-a46a-c43e6ba5dda5', 'Allowed Client Scopes', '6b03f9aa-9012-46b3-a691-480d464101db', 'allowed-client-templates', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('3230d92f-a50e-42d0-b7a6-6a2126d5d86f', 'Allowed Registration Web Origins', '6b03f9aa-9012-46b3-a691-480d464101db', 'registration-web-origins', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'anonymous');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('b7462944-6543-4d77-960b-9b5ff84f2cd6', 'Allowed Protocol Mapper Types', '6b03f9aa-9012-46b3-a691-480d464101db', 'allowed-protocol-mappers', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'authenticated');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('c9be7e93-be92-43d8-b151-591107c7b0c1', 'Allowed Client Scopes', '6b03f9aa-9012-46b3-a691-480d464101db', 'allowed-client-templates', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'authenticated');
INSERT INTO keycloak.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) VALUES ('9231921d-2f72-45af-b752-5369ce56618b', 'Allowed Registration Web Origins', '6b03f9aa-9012-46b3-a691-480d464101db', 'registration-web-origins', 'org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'authenticated');


--
-- Data for Name: component_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('ebac0a78-2f6a-417e-8691-9526efec9564', '04400156-9f11-4656-a136-1266eb39e172', 'max-clients', '200');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('8ad7b6fa-90a1-4fbf-8f93-5535176b2e99', 'f3000c00-1a53-4502-8dc6-6dfb56a4bff2', 'allow-default-scopes', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('629b089d-2eb7-49f4-9170-329a9ff76e1d', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'saml-user-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('6658931f-fab0-4b11-848e-afbc87637938', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'oidc-usermodel-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('c56e1dea-6478-45a9-a536-f489fca471c2', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'saml-user-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('644084d9-3b5b-46c0-b22e-6549ed1ab558', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'oidc-address-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('a0f40b2a-7a7a-4be0-a291-a6a2b46d1e6b', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'oidc-usermodel-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('b55d805c-44b9-4491-b5c1-8716fc5752bb', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'oidc-full-name-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f0688cd3-2931-42d8-964b-c6d545e15951', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'oidc-sha256-pairwise-sub-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('90a7c704-8d71-4e39-bcec-c0b192c9ec57', '705964c9-7ecf-4a27-9fac-5cd07b2b7c09', 'allowed-protocol-mapper-types', 'saml-role-list-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f94a98e6-2470-4523-9290-1f4f005dd299', '97a85410-f644-4c5a-8a29-f5b0ee02da35', 'host-sending-registration-request-must-match', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('76af3aaa-d7d4-416c-8825-afd3b28d6152', '97a85410-f644-4c5a-8a29-f5b0ee02da35', 'client-uris-must-match', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('a048bb3a-571b-4453-afa7-5c353e1b3516', '8b2c49c1-8d44-4ecf-858e-ee951b229d9e', 'allow-default-scopes', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('32ec3e93-1327-4091-b25a-47678865527d', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'oidc-usermodel-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('6acca7c0-00ee-46ce-9b15-fec1bd1bdae7', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'oidc-sha256-pairwise-sub-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('fca5c991-b909-488a-a414-88bb588597fc', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'saml-role-list-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('2a4bc07b-d099-4e2d-877c-2d44d40eb8c3', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'saml-user-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('0fbc03ca-ee9f-4122-9a80-89432b44daf8', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'oidc-usermodel-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f316e812-c410-48a8-80b1-05251bf37123', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'oidc-full-name-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9ac8d548-3e43-490f-ad3e-d1a183ec427c', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'oidc-address-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('d2387a3b-3e7d-4ac1-8baa-c1c4e6eee676', '187808b3-be8d-4cc0-a59c-e65a0c46087e', 'allowed-protocol-mapper-types', 'saml-user-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('fc6383c6-09af-4cd1-8366-d4a2398dd9a6', 'cba1c6e5-7ea1-4a34-86b1-214bab417444', 'kc.user.profile.config', '{"attributes":[{"name":"username","displayName":"${username}","validations":{"length":{"min":3,"max":255},"username-prohibited-characters":{},"up-username-not-idn-homograph":{}},"permissions":{"view":["admin","user"],"edit":["admin","user"]},"multivalued":false},{"name":"email","displayName":"${email}","validations":{"email":{},"length":{"max":255}},"permissions":{"view":["admin","user"],"edit":["admin","user"]},"multivalued":false},{"name":"firstName","displayName":"${firstName}","validations":{"length":{"max":255},"person-name-prohibited-characters":{}},"permissions":{"view":["admin","user"],"edit":["admin","user"]},"multivalued":false},{"name":"lastName","displayName":"${lastName}","validations":{"length":{"max":255},"person-name-prohibited-characters":{}},"permissions":{"view":["admin","user"],"edit":["admin","user"]},"multivalued":false}],"groups":[{"name":"user-metadata","displayHeader":"User metadata","displayDescription":"Attributes, which refer to user metadata"}]}');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('bfe33d8b-4ef2-4e71-b338-d46a3907156b', '9b481e32-d147-45fd-b626-1541c191e4ea', 'kid', '1a12beb9-ecc2-456b-8327-6d800ac23bdb');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('2f13e91c-b431-4b2a-8408-8664bd88a2e6', '9b481e32-d147-45fd-b626-1541c191e4ea', 'secret', 'BueW5q3xZLRxnOqGfkkhPWvtJxEoG-WfYPPwxvcjn7WFd_3k10ysACvGUl4daOI9SBcuJYSNwEaZrQKOCcD7-nOB_cE3KaadDaNoraJHxeJGLiF4Wp4Or8MovIXlgs12s392WAxzWwK3UuV0kyCaYieg0S7W3Q4tHb4PWpZaLlA');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('244e01a4-9f14-491a-ac13-7a2b8cdd10e3', '9b481e32-d147-45fd-b626-1541c191e4ea', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('2a049e1b-4bd8-4d4e-a639-47b150fce7d7', '9b481e32-d147-45fd-b626-1541c191e4ea', 'algorithm', 'HS512');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('5b04c434-2445-4115-b1f0-d5394e8b69ae', '095f8189-21fd-40e1-821c-85567dd9e4e4', 'kid', 'a12745ba-7985-42bc-a3aa-25c84a60e41f');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('cced2492-2d83-404c-8cd6-623d2b4b219c', '095f8189-21fd-40e1-821c-85567dd9e4e4', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9c0182b4-4686-487b-8269-7dad587fdcd4', '095f8189-21fd-40e1-821c-85567dd9e4e4', 'secret', 'YDkvPjlhNb7xwGNgOmoEdQ');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('df5adc4a-2113-499e-bea3-0480ecf057f4', '2a68f012-806b-4374-9e29-41296c866760', 'algorithm', 'RSA-OAEP');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9bcfc400-d460-44d4-a306-e03cbd2b8733', '2a68f012-806b-4374-9e29-41296c866760', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('5937034e-ef23-4e96-ae8a-bcd7ada42dd6', '2a68f012-806b-4374-9e29-41296c866760', 'privateKey', 'MIIEowIBAAKCAQEAofo4Hr44av28XG68xfqFawW9SBkjzvEUg3TslTnDOvekXe7IE2+oAfE2Awfh1jDkWPpzN/75LLgScJz0BRWNb8Z/NmSUXoyf7HiUPqlbjyYvSw95fAcgba0Jeqm/570Ot6dDZ4dTGULBZNvEQ1qZCavkB/ByI4RuDnxFMwlW4lUs/Sdo07ZVOylPeVHMc7HVuZrTVyUQ0xrVdSSwACTHrnvEi0ucgQt3xC1jBPbRKgClszPmEXFcfw+Ak7vz07tp5IpoF01eouUh1ldXJ1StSQXkvV1JCKnTwKV5BS9+wqNEZLQYp4AfBJAC6BXVnfKhgJUPOUevoFjSCyrVzxjvGQIDAQABAoIBAAEWbRNXXry1kyYOvOTaa6EEljKgyPxq4q+gR+j+ACYKKb5THy1/bpVQWvbwJSk0q+/YaXbxVuR6bVTevoYc0Mj0zP/FP9H9TgllMaxuPPxloTDDyMj9qXWhd6kTpAN74dh3WDNFHBh7eeqoTbWcqxIYZ2zrOL6Tm5z5L72QPQpcTWYglpUDo9vs5JYNkQlN88K2rp3lkjLR+7d+b53xMeJ7JD+f14huGJVWX9cIUYjdD2rVVUDgQrQyuEy+VP+Jt2vUG0fcGaigkcpMnzu14frs+rtfJKHF610eKHdhRm2HI5EnK3RG4bJg9Rm6BdYyVl0QNebMRJ2i8bO0sN0VZLUCgYEA5JmIASGfk1aM+61uVeowNBUqucNgmeux8tiEX3EYBMbhwhohtjlRy7HNlnDZFAGGwSYK8VYjrsHwzO142jccmo2IqfviZMDWvKuM//alM/xsy2CeK8jFWj4WHLYtoe7RyCyBAtGo5fLBNiMG/bbeRVuPXT+O5wnAQiibp308zCUCgYEAtWRqX3ZjY8Gs3xlvPDRJTxyS7d7v1jqj0wFL+8CFXzxKFrTxfpHwo9IOmYadVhUFADer25+w7+/knXKkZyXRasIBApHfqjI0jEdvP5TLsblowEQumt6X+11Qr59aKwNd5OGkfmDM6YJJgOOz6GJPSReC94TdkkdxW9F1vz/DauUCgYEA1w1MMexEp6ITjSxxkOd4I3cKM6mGdiaRyChCF1tYQh4rAaP9tOSle1+wTWep/7UT5R55yuHDPcL7Wn3IZFjWUtr1BxyLtUbofKNSSPXqIkbEvmsNQZlld2jS+n2z3hPCTHL5hwJfxrshYmF/US04Wr0w2INTVywILvTuwZkCmfUCgYAI498Cxr6gSQG7/XciMD3XjsL0vZRrn3wf/1RGBm2C+WV4L24WkfiFTupARAS6D1WraQ8XOIBngg5mWRQNqiDVZqS+B4A6yzMgHPAq4ZQKJdgodC8EkBxKyYwGz3yP1x5m9VgmiYABgc0wb/iFTywrnOdiUjS50p6PrXhj4zAksQKBgHpwBOWcUk5tgYUO3mT5zDDsP7ueT08VOt5o+JjtUZGLQBQ/2mMIDgtmkrGX4AsxIQ2mhX+uMrWUHsTr32PLNbI0wYXA9nMIsu+1o7/8eO5MIzttE2QjXUTE9qWQkLOHCvBGT3QXzinomHo/A/zFctzZkLPkQbmPVIlVZlqVKGzX');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('fa5733cd-0b77-4b63-bd1e-0af1f6952143', '065581b9-9f09-4f08-936d-109ead0aa12c', 'keyUse', 'ENC');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('0cb23820-6f27-4d2a-8438-a52bb55cac27', '065581b9-9f09-4f08-936d-109ead0aa12c', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('c94d9831-791e-4f3f-8de0-3527deb117b6', '2a68f012-806b-4374-9e29-41296c866760', 'certificate', 'MIICmzCCAYMCBgGdhcvPmTANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjYwNDEzMDc0MTU5WhcNMzYwNDEzMDc0MzM5WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCh+jgevjhq/bxcbrzF+oVrBb1IGSPO8RSDdOyVOcM696Rd7sgTb6gB8TYDB+HWMORY+nM3/vksuBJwnPQFFY1vxn82ZJRejJ/seJQ+qVuPJi9LD3l8ByBtrQl6qb/nvQ63p0Nnh1MZQsFk28RDWpkJq+QH8HIjhG4OfEUzCVbiVSz9J2jTtlU7KU95UcxzsdW5mtNXJRDTGtV1JLAAJMeue8SLS5yBC3fELWME9tEqAKWzM+YRcVx/D4CTu/PTu2nkimgXTV6i5SHWV1cnVK1JBeS9XUkIqdPApXkFL37Co0RktBingB8EkALoFdWd8qGAlQ85R6+gWNILKtXPGO8ZAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAApRdxsJtz1fcrwY8q/PS46cJc8pt7q9Jub/7Ou79H8Xp9icVi6FHgPxzdf++/AOvtXDnJxf6fgkJ8VUIV7QE183+WrQpwBn/U1Qqk3mXD4Lr3hvU7A2y6JsF20P9c6UAt6hsuYDn8znNlZaCSKiXEZ6q64ykzDjUpGMMAV8k6kqb6i/i6MHod6iLu2CMozW2MBSQ0XqCuWFbwvr+hHhNFzdu+4ekhfVd8TUk7BxQqnQ19rQCUgigtYfOXK/BK6/NwaNEUxhpOON6TzWXzbIsOGliLSU9Q28y3h+y2ZY620WW7tTu+I2ep+6DiSHi1/s6L/mf/dwsSwKASbi37srYLA=');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('dbf7575e-22b3-4db9-8f66-857d6f60474b', '2a68f012-806b-4374-9e29-41296c866760', 'keyUse', 'ENC');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('1abe4555-ce6e-421e-9248-7e8f67eea5ef', 'e75c9aee-9922-4aa8-9a36-d44ee19828e8', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('3782e515-ddec-4f32-a30c-949f02f915cd', 'e75c9aee-9922-4aa8-9a36-d44ee19828e8', 'keyUse', 'SIG');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('56c1f6f0-475a-482c-88da-fbf7507ceda4', 'e75c9aee-9922-4aa8-9a36-d44ee19828e8', 'privateKey', 'MIIEowIBAAKCAQEAqds48DuEx9iLsnIM7E8TOeKFIK2HkNjBuTCGWxnQY1v5vYVjaPvZ0y6M3t3mhJ/Hvw/natIRUX/plIeobs7M/To8n64IWOoFqpu3uIyncepDGZFDJV6Q3jS8l8B9vbW5JXpMWBHSwh+N7rUkqhCTfn6FFEQIYdMMTUWHf+uYRj7AZG0lnlpgxhBWASe+Za+PZacs3ef9uInU5OSJcDgqlVWu3bV7nMYidfB8R82VtA9+tjAGnzBeSIgCjbX4DQjCryW7ubzSWU/Xfwk4DiAszcv6g/Z89MUqoTXdRk+68IvHpD3pKWqoMW/0wBWHyctpvfx0Cou/n6cEZ1fp3f6UjwIDAQABAoIBADpQ4jUUcit8zMWIw6gUJAkxHLzR5yPTT3uJze8UJ0gdqVoopC9EnI4VQtc3fy/Ufas6xhyWH80H6gWNJ8ZXaOid6Hd4NDR2sFhZWxPY8po5MC1kgpWfaIRpvcAqHeGWtQjJetGX2PC+DahBd+ONil4ZCQ6ipvATGfujnfhMxjyDOqMU0a/KEIZrWHt6+cxQacNXtHerReK+LHXbSfDoDPLdpgzJSzJv5ybiZ64FN8g+eaGEf/+UzYegpgw2G/nvPyVaTOZ/EGBWs+gT0nkUQsWxDNTfV9jdgb/qQ0W0IvHS+4w59jfhxeMgqAfPYUoKHxbb5BqwIa1WqsC8iARGyEUCgYEA1oTbxOjC0de3b9bFMmlILC9eQDvbWNimPbTzghVeKOi+QTOHgcJ4O1RsP4XkFcGxSvWADAW+yPk+S0xd4D4lobWi2krQRry+2VHFG5VuXLtYP1/RIXBJzFTHvGQOdCEmmJTw+s/LDTd5eHG4a2D6jRVsoMkVXZQVlUbdXthDkmUCgYEAyrN4FpJ48YpM629ybq9+vTGpBtqcKkr9nUYegcq6FTXZT5bJ01TeGEuuVtGLxiQM+rv7N+ItQRagN5hnNLZWcd4jNbV84dCD5+tQSlAIyjryW18rqHvte86bIsRlTUXkm521Cq6RctxC5S3HjWIsIv0kfunI19e9U9mwr5G14eMCgYAZ7JRih36DvX39lgbewLpoHJFXUeSAKC5u5p9G6S4n43iaiI+nrsi44sryIkweFPpIBMMksM0NnJFaqC/wGZKSqFC18LSa19R4jtkzLCvaKQnRHtM3J0rD1rsMmUrl3du8NMOqi9IOFtYnKBcRYvbkdeJay/I5DNxO3fGCtL/1wQKBgCfT3ZupygPDpdt4uWZQKznnYQvMtnSE6ZIWbfYYrDlwrDM8MInKmhzx+d5rK+iRus8lUnYnhbbNSEvEMTslPJUBDbAG6fPAsbpG/S6szR1XObmEWKKxPvddoBPTvQfS3NlKwoDHziJgbvBy70uzZ3K0hJA/RUxLwpKQKmxE2BT7AoGBAKYpNXD7eVYNIQq1oCf0PY9RM2A8C0lVoAbPY77B/4sQqpg0EZQTzjifo1Xn7/9mzD4VNeeS2Sf7UUHYosmz4DVgWhfldgdQml1qMp0Xeew1U4n//n3JcJidCNd8C8t4kp9r5YjiLIiT4ggIaw+g6XY6fcdTGvxGZKvH73wAuF5I');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('828e0255-b88a-4ea2-8099-0b171a338d79', 'e75c9aee-9922-4aa8-9a36-d44ee19828e8', 'certificate', 'MIICmzCCAYMCBgGdhcvOnjANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjYwNDEzMDc0MTU5WhcNMzYwNDEzMDc0MzM5WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCp2zjwO4TH2IuycgzsTxM54oUgrYeQ2MG5MIZbGdBjW/m9hWNo+9nTLoze3eaEn8e/D+dq0hFRf+mUh6huzsz9OjyfrghY6gWqm7e4jKdx6kMZkUMlXpDeNLyXwH29tbklekxYEdLCH43utSSqEJN+foUURAhh0wxNRYd/65hGPsBkbSWeWmDGEFYBJ75lr49lpyzd5/24idTk5IlwOCqVVa7dtXucxiJ18HxHzZW0D362MAafMF5IiAKNtfgNCMKvJbu5vNJZT9d/CTgOICzNy/qD9nz0xSqhNd1GT7rwi8ekPekpaqgxb/TAFYfJy2m9/HQKi7+fpwRnV+nd/pSPAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAH/ziHN4q+PhCFcqYCIHHNerbBjRNQlhb/whTECPiGWHmrBXt8VyXYcliSS9EImQTper8w+Cjgi8i2jw2yCHRgRAatvh0p1ZxQwPZMMIFJy9M41VVwKuMIPNN4+MO5mn9mfiBr9TkmbxG1EAni8hujZVnUc+VJVRCBCmYzUEuOCGewX2vO4JjdAK6jfq+totcGPJ593L3cGRGnD0vI8Ic9EjVSLOX712iKmYC/KY2+2PfQzGWTI0d6wu6Le0SGtijnMl9W5dItUnYLqsjxIZw9OMTeNWCTVBk05XmnneA3O1OPsfIn9v9QXmtIhGXxodiklTp2x4Qvv2wPdIraMRpPY=');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('23503ac2-c23f-4119-83cd-d163380f8d54', '5a0de682-35b7-4393-bbf0-f8060dfa96c5', 'secret', 'pjmuolI3H12vl9xq564Fkg');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('03ae97f4-8cb8-4024-ab21-a1be523bffec', '5a0de682-35b7-4393-bbf0-f8060dfa96c5', 'kid', 'c09bccf9-7741-4c4c-a97b-1b3eb9117db8');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('6062ea70-64e9-45c5-ba6b-73478dbf2906', '5a0de682-35b7-4393-bbf0-f8060dfa96c5', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f6e4b3b6-bcc8-4409-8b57-e9edba4184e5', '51695a6e-fb22-4cb4-9d26-c6c0e781c1b1', 'algorithm', 'HS512');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('42b8347c-b9ac-4f6e-842c-15ff8f171b6e', '51695a6e-fb22-4cb4-9d26-c6c0e781c1b1', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('71c03a86-3653-4c79-ab6f-23a89b5ca8cc', '51695a6e-fb22-4cb4-9d26-c6c0e781c1b1', 'secret', 'fJYXvj_upCZMibhm1PfDF9aVRYUHJudJMer26duuyCkQEL6x9XC1TtlU8I7lXUnd3HB0sWwKb3eBcRGZIQBIfXUtTkChFP7eqyrqGjVEL0bhwyrKT5kVyFjhroDw1xRAmr4WKLv1NyzE4vCs5YsBCzAl903VtZX_Ee9KIUxhOvY');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('4d7d6861-7035-44a1-9918-9720b583c2cf', '51695a6e-fb22-4cb4-9d26-c6c0e781c1b1', 'kid', '58c3241b-77fc-4231-b95b-448ce8bad01a');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('c49d94c2-b4b6-4cd7-81ca-c4f32d5833e2', '7d007295-df3f-4c29-b261-49f3f3b8db45', 'priority', '100');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('b6c3fc7a-df17-494a-8168-f99b3b4c7def', '7d007295-df3f-4c29-b261-49f3f3b8db45', 'keyUse', 'SIG');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('0c99f6d9-8168-46f0-a859-a04684bec39b', '7d007295-df3f-4c29-b261-49f3f3b8db45', 'certificate', 'MIICqzCCAZMCBgGdhcvUszANBgkqhkiG9w0BAQsFADAZMRcwFQYDVQQDDA5hY29tLW9mZmVyZGVzazAeFw0yNjA0MTMwNzQyMDFaFw0zNjA0MTMwNzQzNDFaMBkxFzAVBgNVBAMMDmFjb20tb2ZmZXJkZXNrMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkeWLXKT6s5F4/6kF3kpLsRPl0iaB4Wxfd51sZeNADFjKUSaBi1ZgURpo0UC3RdXQERKWHYgWarTiespxTlp5YVre3ygBihtv1zWtgWmp/ESgckdOqqfyXLlDJyYvHCrYheGfPeN+qGxV9adIQq8IE2cFPHHZDpi/X0uBzx+P3x0iMGidZXrtfNBkTPhrymHLgomjh4lXMCiMHaC07C/B2uerfz/0kSgP/PwHznsHNXZNV01aakELP79FWMYJbVfrmHX88E1TYbcAY0aRPPnHAuHNhed5JjoGT0OmG/B9VMsRylLcCE/dnoVHS4HhpazjvhvUdyVvcsSwFS8BQzafzQIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQAoKQ4ZbWULBM7WVwuBrDAoBkqXntYTRFaUK6Avr36YRCqUnrerAQLVDLAtL8zd94PDN7PCmcUsPKGa50Une9jLENy2CY8bvdO02Kzovi49Djq4H/doSTPSzsAR6dLOcgFOcBwTTrk9v1AMc6EWgKfWsPvAN27bm709cESHjBNyhLps62OF7ove7rGHkNFuSdrz+m/sYNVHYI7tx1h3rnJ0YJN8dAJWEExtZzLALHQ332Um+YCVFRcbk56fYROBvr19YAGyKQ9+j0qyOnLfoZVGACPnxAq5C7iMxgXdbWNm82BM7DXvvH0XPi4HXucQWmhREBXvQlJiey1G8hKmL8X6');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('387d7aa1-b77b-4760-81e4-674d58acd5da', '7d007295-df3f-4c29-b261-49f3f3b8db45', 'privateKey', 'MIIEogIBAAKCAQEAkeWLXKT6s5F4/6kF3kpLsRPl0iaB4Wxfd51sZeNADFjKUSaBi1ZgURpo0UC3RdXQERKWHYgWarTiespxTlp5YVre3ygBihtv1zWtgWmp/ESgckdOqqfyXLlDJyYvHCrYheGfPeN+qGxV9adIQq8IE2cFPHHZDpi/X0uBzx+P3x0iMGidZXrtfNBkTPhrymHLgomjh4lXMCiMHaC07C/B2uerfz/0kSgP/PwHznsHNXZNV01aakELP79FWMYJbVfrmHX88E1TYbcAY0aRPPnHAuHNhed5JjoGT0OmG/B9VMsRylLcCE/dnoVHS4HhpazjvhvUdyVvcsSwFS8BQzafzQIDAQABAoIBAAeJrouY0oMYjwHWf8EeYY7CkmsrJia5bK1HauRQu2xn4fwTWzoRumQ2UxgMmet3woo/RZY9A7t7oP/rGbOMpRzMjxtEe9/gzwR1d4NqLCgme4ur93qFttXnlHqfVGvGIu233HxcFp0pC7/nZqpbVLV76x9WWnqQlcKcqhZDcTF7wd86YTPcSFyxrAZDfuBW2uUTbCwdwL3xqHwq1mwqinfiQx3Mrkg0a4WR5WZrmgxLwjDoMYzxG+h2gXYVfCVzz1C4Sfh2K1hjkV2YSDtsB5n4uwkG8ICqRo/81OEfXAYHUdkqZLYQzBgtd+F7IPuH1ZeaoDGgUprh0FPwB11tilkCgYEAx9tk+/Mw7CxsklsxtdUnSyxJB4OMrS7CRvTJXSsIvwUrySCsl8mGtyCYpXGzTCXCRXQEwNyC7ODGw53qUHvD6U7GfhrKXpeVVWqbnfSgG5gVwo5ZFcbwJngst0gDMh4FD5irkgAnRhogHAvhY83X1I+bmWOV6Eda75KjdRGklV8CgYEAuuGfCvk1Rb0bo2BY/ygOQSLREpmKSKYJsljThJaW2/EMQLhpBGfcVwwQS87eYH5nezYeOecO88MKga9yKOuIdXhwih47wCBAr0TA45Q9A2v7S7QeOar8g0d8LbwrNB/9gyPgAKju0TS9eL95mGgGklLtHi0ThIIGd1e5uDyxDlMCgYAFvgUBxDQEpSYdcmdUPSKa41PZ1mrFUxGb7k6W0bS3oFNovPqYhd7MBjC8mC65omAZlMLKM8vDOJYdar0fwN6ZJn1HhEeKPjq5MI32FOBAyrbdVy+yE3w07sECJxyIZRpqH03WrRBz0C5Z//Fi57gq0FF9L8JP4TT4qzLtGyuqawKBgF+RwE7RUQAADKFJRVn/NwLydi7n3EL4vl65dDoK9M03gUebxwDcyF6vqanK+ggovGzTKTP9SLU6GiZl/aCViuxgElVfzribBdlb9LSte2JDl3iIfSiKm6XbKdMNtp5qea/V6dkMi0zrhrW4Xcul7y5nQCG9dYy/HeVsNGrWhslHAoGAbxpUFix7KdpVsIUcNudaT374fQRZg0iURrwySirUYZQMLJFltAkFwz0mzDxKK+CO9W6poHaflmtNYphFhjRVE77RDI6PSui9X53lEXjkOI2bGf4qbmzv9SBMGsXGvPJHqnarHnH79caxYA2wc/fCSLQLC8TE9kd8riEwFkFoXQQ=');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('c7b2cc7c-0e47-4cda-b547-7521d35d7a26', '065581b9-9f09-4f08-936d-109ead0aa12c', 'privateKey', 'MIIEowIBAAKCAQEAyWQjUP3fFIIquX4pPZe11v0nz27Q6hUQsnDL+NxWR8z8JVSDYcOazb8vn9L5xPxyIxfONjmb5/fKiypanuQEqBx254UgmsWbl8dl6B/gumc53BQxviS7w9whB5YOdLglEf2QtnroTIblMMzqqhUMynYhaUIHWn9SIuDI6z9Bff8RhKpL+0I0pX8woRWzXyls5NRdJDFHFiBSwcnplEdpl9KVLfAcNWmcHtZ8Zb1VKTVNNNducr7K8fRXdxfHzGzC0ZlrwK48HTSsRTHGQ67ei5hNqDbdrAfQIek/xPYmoFLR9/jRK9ptK5f3br+m3T+K/0hMBU0931QDhHxvj9SMKwIDAQABAoIBAC7Shld9PtFg1hgcWfBFBnT+lLPoms/hp+kkyneImtLEuNbhCE7BkItHaQYqogGHg+3eygXXbQUImmGyrjEE6IRBYe/ABu2VBfDK3kmSp8gO2efuFgaUOcd2tYMzAxdl/NBq+KtEdh/cuQqYifKTRE8KGgiD3nvO4ETVqEDxiwOE0WO4Bb7cq3c4m7KMpfKwSjNqHYcM/aH772Zld8FYFL95TqTSPx5wTQEVA6kC6KF+h1PqmLa2KcyO8Mtc3Q+eNY3u9J7EjGHLtMdERRMRGnyek8+8a9/tYATWdR5EorSsIIcMbNM0XSInYLZxYSm0sMCz/sCaKLgDgSrpjLLcMxkCgYEA6ww890E08PUac67tVs1lYfSwNoQDWF5SRyF6XgZNKoZ/uJIWONV39Z9oyzNSuqgGpu5n1xaTFrPOSKIIACHXwhb4Tse9uUUTiuqxUiUn1vRD1ltpdF7r8uHiRl2rfCt8Luv8rSuVNa1v0i9FC40RvBfPXINrDus9sjwXKTXj068CgYEA21fcAm+3XwJ3Vp+5oh7oozqqgthAzjmRXqtEb96PEeWOPDjpILzyyRF22mjtQXffJjEqtmdLkUAitWTz8zT8YLZAoZ9i39mW8pAHlHkECcNdZaL9GYXxcS5gwrhck40aKFg6xxRtvFB/1U+SrDJtLLcsVMqzkkvNcpezuec04kUCgYEAzu4CSme01SHj/M6XEqFXTSrfa89DJqw7YXX+xgJkMzkf/n1WZQjCSJLj7mkrvzqoSJSBBOJR8l2wEU/dHUiuK6iPSMQeqpo+v0EphTlC3sJDatclexcKQNVOoUZb78BU3vZRiJ9jCFO9q1yEO8whPef0Xe0w9nxx35V5ioVwIu8CgYBAU5/+Ru0sO/jruqQiW5Y2aLog7XL0CAYOEYRcmpSy1vPDzZzxMPiy5yBIJYWPMayL8tdn7xtGWdzT/etdZCiv5ENIIwpIQ/P05zCR5nu8sULuz8ISfim027kc4hykWTlWo6l5QRB9rc4PrOqC/bbu6jliFKBdQ0XZWYwn9RqZUQKBgCqcqj0Ou/sSQWGBpTqnSNBnRzB4p+xJsFQeZCK4EyBqyo9blRLKuwGpAqJCSR4odGjKL4J1YKg+0PGvBOQ86s+DxRCdKNS+c73wRSuqOKfosqwIPdkqqvKqRRt1rh7S4NrwLWhAWgcBuGJtH6vvxOS+9OEKXIUOFlH0clHgNsPD');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('8b52d41d-6fe4-4722-af43-0bb1cbff9605', '065581b9-9f09-4f08-936d-109ead0aa12c', 'algorithm', 'RSA-OAEP');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('ceca041e-7dd6-469d-8b35-6bc20daaeef3', '065581b9-9f09-4f08-936d-109ead0aa12c', 'certificate', 'MIICqzCCAZMCBgGdhcvVyTANBgkqhkiG9w0BAQsFADAZMRcwFQYDVQQDDA5hY29tLW9mZmVyZGVzazAeFw0yNjA0MTMwNzQyMDFaFw0zNjA0MTMwNzQzNDFaMBkxFzAVBgNVBAMMDmFjb20tb2ZmZXJkZXNrMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyWQjUP3fFIIquX4pPZe11v0nz27Q6hUQsnDL+NxWR8z8JVSDYcOazb8vn9L5xPxyIxfONjmb5/fKiypanuQEqBx254UgmsWbl8dl6B/gumc53BQxviS7w9whB5YOdLglEf2QtnroTIblMMzqqhUMynYhaUIHWn9SIuDI6z9Bff8RhKpL+0I0pX8woRWzXyls5NRdJDFHFiBSwcnplEdpl9KVLfAcNWmcHtZ8Zb1VKTVNNNducr7K8fRXdxfHzGzC0ZlrwK48HTSsRTHGQ67ei5hNqDbdrAfQIek/xPYmoFLR9/jRK9ptK5f3br+m3T+K/0hMBU0931QDhHxvj9SMKwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQA+Lw3eohrbkEKWp68eEn+0/6zdOMDdqqjJcsEI+rARk8F9BFAL9TxQqR+FB2yHffBzNQI78UxzHvBPVpdgc0Dp19HzjEAcQ5+83qc+/EBux9imdLLp97Bqz6KS4Bi8XziWuWg39VYpnQDIKuECGcjcK2SO4ECHuXcJbH/T6QK5owZhQkQjJ8W2DXJ+h4h6chQUgaq7uj+c1uMPBxpVXVybV6TADGMavsi5zVmm7NN1k0IhGKujxStvkn0XFHh8se9ijVbC+ezg/N1hxyud+Sayh73A+lPWszWzBctsl59g/wrgx3RTCBMiVBadR05AUmN/343xJVt8tB6JMz31bFat');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('a85a2b16-9cda-48b0-9d8f-d1a0a6409f35', '4d2c521f-c1bf-4d59-bc61-5ba801793421', 'max-clients', '200');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('a6c94aaf-7b6a-4be3-9b20-8f690e8aa2d3', 'ad114bf2-9f8b-4435-8d57-23d9f959096d', 'host-sending-registration-request-must-match', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('34626dc1-94cc-435a-8f25-206875572d1a', 'ad114bf2-9f8b-4435-8d57-23d9f959096d', 'client-uris-must-match', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('2f20645c-6ad5-43fe-abdb-4e1e6c357649', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'oidc-usermodel-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('8e509383-5e55-4811-9322-bac5b68f4b8b', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'saml-user-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f84734a3-0159-4701-9fcc-072f277c0ecb', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'oidc-usermodel-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9cb39167-6845-4a35-9fb8-be0d6f946b50', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'saml-user-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('d82892c9-2a0a-4567-8f27-4d4cc355e910', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'saml-role-list-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('ac2f29ab-943e-4225-b4a5-6f91e5ac0112', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'oidc-full-name-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('6b6ece60-05df-4f3c-966a-d3e0701ebd8a', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'oidc-address-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('027b489c-459d-4d48-a3b4-c117fef3fb16', '157edc3d-16af-4384-89e6-22091a452c48', 'allowed-protocol-mapper-types', 'oidc-sha256-pairwise-sub-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('f9f32c6d-1c15-4c76-9860-85869305397e', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'oidc-full-name-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9e6d5151-d2c4-4f0c-ba25-ca2309b7b855', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'saml-role-list-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('c3804fa3-eda0-4246-80a7-0753461a1b65', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'oidc-address-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('5edadb4c-3a0f-4ee8-9d43-a3d90b5eb920', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'saml-user-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('d94b96bb-071c-4de9-95b5-a3ceb11639d7', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'oidc-usermodel-property-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('7d98c711-7085-41b5-aa45-6a57635eb601', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'saml-user-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('4a3a11ea-936d-4f02-892b-431850066405', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'oidc-usermodel-attribute-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('92c932bc-92a6-4edc-be7d-77952ff0e1b8', 'b7462944-6543-4d77-960b-9b5ff84f2cd6', 'allowed-protocol-mapper-types', 'oidc-sha256-pairwise-sub-mapper');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('9ce8bcc4-dd5c-4e09-8781-f6338bf8471d', '00b0f07e-270e-41d4-a46a-c43e6ba5dda5', 'allow-default-scopes', 'true');
INSERT INTO keycloak.component_config (id, component_id, name, value) VALUES ('4180a7df-b502-43ba-904b-31ea0ed498ac', 'c9be7e93-be92-43d8-b151-591107c7b0c1', 'allow-default-scopes', 'true');


--
-- Data for Name: keycloak_role; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, '${role_default-roles}', 'default-roles-master', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('546b6682-985a-4276-85e8-f6b238c0d814', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, '${role_create-realm}', 'create-realm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, '${role_admin}', 'admin', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('84596bf9-685b-43ce-a8fa-9ec034c6effd', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_create-client}', 'create-client', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('0a48ca97-0424-4515-a718-142f0bd81bda', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-realm}', 'view-realm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('d9cfdf78-b750-49fc-9c7b-78c58cb21b3f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-users}', 'view-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('1493b741-cf69-4b2c-97e4-0afc3fd8eeec', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-clients}', 'view-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('0c496473-6de0-4856-b992-04c08c6ba9a3', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-events}', 'view-events', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('af58b34f-e4cc-48e7-b931-4332edef69ec', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-identity-providers}', 'view-identity-providers', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('39694c98-df86-4314-b3e6-0bb99e3ba667', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_view-authorization}', 'view-authorization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ed4808a9-1664-492d-89f3-db28b4e659eb', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-realm}', 'manage-realm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('37a32190-496d-447f-82ce-f9daf3db4b51', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-users}', 'manage-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('2de9e9c8-b7c7-4a03-a5ad-fbc30c155967', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-clients}', 'manage-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ce5b8b67-6fef-4a76-99c2-aa5178bf73ad', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-events}', 'manage-events', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ed50e3ae-3a2e-474f-bad1-f16357d5b6ae', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-identity-providers}', 'manage-identity-providers', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('90116158-c3f0-466e-9075-e46fef8acf42', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_manage-authorization}', 'manage-authorization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('70f2be0f-4433-470e-ac54-0ad007e19af9', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_query-users}', 'query-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('b5b6c20f-8ea0-4ba8-a35a-97e05363510d', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_query-clients}', 'query-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('a636fea8-f94e-4f2e-87b7-7fab7ab6cc7f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_query-realms}', 'query-realms', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('4d4cba41-c227-4654-9c6f-0efbc1ad1d7e', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_query-groups}', 'query-groups', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ef0cea9e-f169-4bdd-8126-ff52d09aec12', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_view-profile}', 'view-profile', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('a0765113-d540-41c0-bee1-e7a1766903fe', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_manage-account}', 'manage-account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('744c03c7-5047-41e1-84fc-40a41ef6639a', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_manage-account-links}', 'manage-account-links', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('1db329a0-9847-4aa6-9fb8-dddd0a35031c', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_view-applications}', 'view-applications', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('6d2083c9-1645-475a-a09c-2ee60a49846b', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_view-consent}', 'view-consent', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9691e2b5-6dd0-4a09-bfa6-8e029a833ed3', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_manage-consent}', 'manage-consent', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('df575729-d8d6-4b2c-a925-4f5aadc0136b', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_view-groups}', 'view-groups', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('5bc29832-ea48-4356-afc1-1cc56ac9765f', '2e3b661d-6818-4c49-8d14-202bae329f7f', true, '${role_delete-account}', 'delete-account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '2e3b661d-6818-4c49-8d14-202bae329f7f', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('884ee811-e43d-4565-bb64-b34eaf4e6986', '8cab183a-28a5-4d7d-bc0c-098b0525f089', true, '${role_read-token}', 'read-token', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '8cab183a-28a5-4d7d-bc0c-098b0525f089', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('210032f4-cba2-4d77-b8e5-d247ed1a321c', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', true, '${role_impersonation}', 'impersonation', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '23fc1943-a349-4d6e-bf25-888a75ee3d7d', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('6f50235d-13da-4f67-89b6-2efd74cb80af', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, '${role_offline-access}', 'offline_access', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('f84f1cb3-9ee6-4216-bf88-77edc57d0e4e', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, '${role_uma_authorization}', 'uma_authorization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '6b03f9aa-9012-46b3-a691-480d464101db', false, '${role_default-roles}', 'default-roles-acom-offerdesk', '6b03f9aa-9012-46b3-a691-480d464101db', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('3b584950-466b-434c-a8b7-fee9e9ce9fcc', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_create-client}', 'create-client', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('e91b1192-b0b9-497c-9d10-dea7107c5ea5', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-realm}', 'view-realm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ede85a0b-1323-47ae-aab1-37636183645d', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-users}', 'view-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('93b05805-80e2-4371-979a-d62c6f7da2bd', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-clients}', 'view-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('960bb0fb-bbc5-46cb-9118-cb825993d5a2', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-events}', 'view-events', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9c39126b-4e67-4a2a-b1b2-d7be1b51f867', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-identity-providers}', 'view-identity-providers', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('79d7de4f-5621-474a-a4af-1cca9c942a23', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_view-authorization}', 'view-authorization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('541ac999-6cb1-4917-ad8f-e4264f1b9a4c', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-realm}', 'manage-realm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9600e427-f117-43c1-9f48-2565c29cb043', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-users}', 'manage-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('956ad9a6-9fcd-457c-bf8c-08ce1dd16e2a', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-clients}', 'manage-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('f282dc05-9788-4fd1-afb3-6d6b2c278865', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-events}', 'manage-events', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('e447edd0-c7c8-4d41-8b3c-5c9c71a4f1cf', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-identity-providers}', 'manage-identity-providers', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('18915831-dad1-4c1f-9567-ba273ca9cff1', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_manage-authorization}', 'manage-authorization', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('a20d2871-ffb1-408f-b3b5-9ff3ea64ef14', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_query-users}', 'query-users', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('fd9bef3c-8f35-45f9-acba-98fcbde675e8', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_query-clients}', 'query-clients', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('2cbc89d2-5bd1-42b8-9025-a7c218d8aa32', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_query-realms}', 'query-realms', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9ad75136-eb96-414f-b63b-675914b4ba4c', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_query-groups}', 'query-groups', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_realm-admin}', 'realm-admin', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9a0a3813-1077-4101-b611-7c7ce45caf1e', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_create-client}', 'create-client', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('70d761d0-c804-4d6b-8036-b1792d8da606', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-realm}', 'view-realm', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('c98d1580-f1f0-4dd0-a10d-4759653b67ac', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-users}', 'view-users', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('c996b9c4-a395-4458-a272-cbd70cca5697', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-clients}', 'view-clients', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('fb90a13f-cb08-48a1-99c0-77cfcbc8c269', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-events}', 'view-events', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('35933b1a-de62-4281-b6fd-fe93b9a8bf04', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-identity-providers}', 'view-identity-providers', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('304a6e1b-b000-44be-9a16-f0839c0445d8', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_view-authorization}', 'view-authorization', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('02d9d003-3872-4ba9-83b0-01ca074c3ed7', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-realm}', 'manage-realm', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('93cc749d-a4ca-466f-ae90-1df594026a86', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-users}', 'manage-users', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('39091b8a-7c3d-4bcd-be9e-3b2ab657dbd5', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-clients}', 'manage-clients', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9919db08-58e3-4901-b771-503865bacf82', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-events}', 'manage-events', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('c5f5764f-dacf-423f-b21d-00d9782ff352', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-identity-providers}', 'manage-identity-providers', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('85258334-fcc3-457a-85be-5b97dab5db43', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_manage-authorization}', 'manage-authorization', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('86106f7b-72e4-4d5b-a95e-8fd4b09de761', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_query-users}', 'query-users', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('ed2038bc-42a9-4180-a6a2-5b1c8e017a8b', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_query-clients}', 'query-clients', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('78e69fba-db88-4f8f-a8f3-f9f0ccfa22dc', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_query-realms}', 'query-realms', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('7e35e5e4-0466-4270-85f3-f9ad9eb6de6d', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_query-groups}', 'query-groups', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('3d7db414-3ff0-4395-864d-3e92465c12ae', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_view-profile}', 'view-profile', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('33f73a3e-d8fd-42ce-81b7-0dfe1610a708', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_manage-account}', 'manage-account', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('10076c17-a0de-4209-9810-c358d5e91228', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_manage-account-links}', 'manage-account-links', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('87ad1546-6af3-4f20-b73d-cb7a6e0dc152', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_view-applications}', 'view-applications', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9ed59882-1d21-472a-9d68-a0cd58e7252c', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_view-consent}', 'view-consent', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('8f5a8b97-b638-4ae4-9a4f-2e8510d1da05', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_manage-consent}', 'manage-consent', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('8ab6958f-237f-4dee-b793-915d02b7a279', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_view-groups}', 'view-groups', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('d5b87d96-0a38-4db5-ad99-69c6676a0634', '5741792b-35db-4f5f-9aba-26f2c5b81be5', true, '${role_delete-account}', 'delete-account', '6b03f9aa-9012-46b3-a691-480d464101db', '5741792b-35db-4f5f-9aba-26f2c5b81be5', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('40d2a207-c8cf-4586-b59e-499e5a299052', '4c572e75-71db-4855-abac-3ae9c6d8f873', true, '${role_impersonation}', 'impersonation', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '4c572e75-71db-4855-abac-3ae9c6d8f873', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('c0ada4f0-5cfe-441d-ba92-a21f04a92ea6', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', true, '${role_impersonation}', 'impersonation', '6b03f9aa-9012-46b3-a691-480d464101db', '44cb6ea7-95da-4e10-8b67-0f6cd9558a58', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('9d5b68ba-e6f5-4a8f-bcf4-6ece75cbfb7d', 'ca6be0ae-5a10-46db-8217-aff854173617', true, '${role_read-token}', 'read-token', '6b03f9aa-9012-46b3-a691-480d464101db', 'ca6be0ae-5a10-46db-8217-aff854173617', NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('dc258724-34b8-4804-a513-50f2aa6ca988', '6b03f9aa-9012-46b3-a691-480d464101db', false, '${role_offline-access}', 'offline_access', '6b03f9aa-9012-46b3-a691-480d464101db', NULL, NULL);
INSERT INTO keycloak.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) VALUES ('7e18b1d3-f219-4b2b-8afc-a3a7280fec54', '6b03f9aa-9012-46b3-a691-480d464101db', false, '${role_uma_authorization}', 'uma_authorization', '6b03f9aa-9012-46b3-a691-480d464101db', NULL, NULL);


--
-- Data for Name: composite_role; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '546b6682-985a-4276-85e8-f6b238c0d814');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '84596bf9-685b-43ce-a8fa-9ec034c6effd');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '0a48ca97-0424-4515-a718-142f0bd81bda');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'd9cfdf78-b750-49fc-9c7b-78c58cb21b3f');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '1493b741-cf69-4b2c-97e4-0afc3fd8eeec');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '0c496473-6de0-4856-b992-04c08c6ba9a3');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'af58b34f-e4cc-48e7-b931-4332edef69ec');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '39694c98-df86-4314-b3e6-0bb99e3ba667');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'ed4808a9-1664-492d-89f3-db28b4e659eb');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '37a32190-496d-447f-82ce-f9daf3db4b51');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '2de9e9c8-b7c7-4a03-a5ad-fbc30c155967');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'ce5b8b67-6fef-4a76-99c2-aa5178bf73ad');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'ed50e3ae-3a2e-474f-bad1-f16357d5b6ae');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '90116158-c3f0-466e-9075-e46fef8acf42');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '70f2be0f-4433-470e-ac54-0ad007e19af9');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'b5b6c20f-8ea0-4ba8-a35a-97e05363510d');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'a636fea8-f94e-4f2e-87b7-7fab7ab6cc7f');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '4d4cba41-c227-4654-9c6f-0efbc1ad1d7e');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('1493b741-cf69-4b2c-97e4-0afc3fd8eeec', 'b5b6c20f-8ea0-4ba8-a35a-97e05363510d');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('d9cfdf78-b750-49fc-9c7b-78c58cb21b3f', '70f2be0f-4433-470e-ac54-0ad007e19af9');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('d9cfdf78-b750-49fc-9c7b-78c58cb21b3f', '4d4cba41-c227-4654-9c6f-0efbc1ad1d7e');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', 'ef0cea9e-f169-4bdd-8126-ff52d09aec12');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', 'a0765113-d540-41c0-bee1-e7a1766903fe');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('a0765113-d540-41c0-bee1-e7a1766903fe', '744c03c7-5047-41e1-84fc-40a41ef6639a');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('9691e2b5-6dd0-4a09-bfa6-8e029a833ed3', '6d2083c9-1645-475a-a09c-2ee60a49846b');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '210032f4-cba2-4d77-b8e5-d247ed1a321c');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', '6f50235d-13da-4f67-89b6-2efd74cb80af');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', 'f84f1cb3-9ee6-4216-bf88-77edc57d0e4e');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '3b584950-466b-434c-a8b7-fee9e9ce9fcc');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'e91b1192-b0b9-497c-9d10-dea7107c5ea5');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'ede85a0b-1323-47ae-aab1-37636183645d');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '93b05805-80e2-4371-979a-d62c6f7da2bd');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '960bb0fb-bbc5-46cb-9118-cb825993d5a2');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '9c39126b-4e67-4a2a-b1b2-d7be1b51f867');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '79d7de4f-5621-474a-a4af-1cca9c942a23');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '541ac999-6cb1-4917-ad8f-e4264f1b9a4c');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '9600e427-f117-43c1-9f48-2565c29cb043');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '956ad9a6-9fcd-457c-bf8c-08ce1dd16e2a');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'f282dc05-9788-4fd1-afb3-6d6b2c278865');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'e447edd0-c7c8-4d41-8b3c-5c9c71a4f1cf');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '18915831-dad1-4c1f-9567-ba273ca9cff1');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'a20d2871-ffb1-408f-b3b5-9ff3ea64ef14');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', 'fd9bef3c-8f35-45f9-acba-98fcbde675e8');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '2cbc89d2-5bd1-42b8-9025-a7c218d8aa32');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '9ad75136-eb96-414f-b63b-675914b4ba4c');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('93b05805-80e2-4371-979a-d62c6f7da2bd', 'fd9bef3c-8f35-45f9-acba-98fcbde675e8');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('ede85a0b-1323-47ae-aab1-37636183645d', 'a20d2871-ffb1-408f-b3b5-9ff3ea64ef14');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('ede85a0b-1323-47ae-aab1-37636183645d', '9ad75136-eb96-414f-b63b-675914b4ba4c');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '9a0a3813-1077-4101-b611-7c7ce45caf1e');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '70d761d0-c804-4d6b-8036-b1792d8da606');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'c98d1580-f1f0-4dd0-a10d-4759653b67ac');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'c996b9c4-a395-4458-a272-cbd70cca5697');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'fb90a13f-cb08-48a1-99c0-77cfcbc8c269');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '35933b1a-de62-4281-b6fd-fe93b9a8bf04');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '304a6e1b-b000-44be-9a16-f0839c0445d8');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '02d9d003-3872-4ba9-83b0-01ca074c3ed7');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '93cc749d-a4ca-466f-ae90-1df594026a86');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '39091b8a-7c3d-4bcd-be9e-3b2ab657dbd5');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '9919db08-58e3-4901-b771-503865bacf82');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'c5f5764f-dacf-423f-b21d-00d9782ff352');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '85258334-fcc3-457a-85be-5b97dab5db43');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '86106f7b-72e4-4d5b-a95e-8fd4b09de761');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'ed2038bc-42a9-4180-a6a2-5b1c8e017a8b');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '78e69fba-db88-4f8f-a8f3-f9f0ccfa22dc');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', '7e35e5e4-0466-4270-85f3-f9ad9eb6de6d');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c996b9c4-a395-4458-a272-cbd70cca5697', 'ed2038bc-42a9-4180-a6a2-5b1c8e017a8b');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c98d1580-f1f0-4dd0-a10d-4759653b67ac', '86106f7b-72e4-4d5b-a95e-8fd4b09de761');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c98d1580-f1f0-4dd0-a10d-4759653b67ac', '7e35e5e4-0466-4270-85f3-f9ad9eb6de6d');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '3d7db414-3ff0-4395-864d-3e92465c12ae');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '33f73a3e-d8fd-42ce-81b7-0dfe1610a708');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('33f73a3e-d8fd-42ce-81b7-0dfe1610a708', '10076c17-a0de-4209-9810-c358d5e91228');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('8f5a8b97-b638-4ae4-9a4f-2e8510d1da05', '9ed59882-1d21-472a-9d68-a0cd58e7252c');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '40d2a207-c8cf-4586-b59e-499e5a299052');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('4de940e7-aee7-4795-9f55-eec0a3d7cd0f', 'c0ada4f0-5cfe-441d-ba92-a21f04a92ea6');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'dc258724-34b8-4804-a513-50f2aa6ca988');
INSERT INTO keycloak.composite_role (composite, child_role) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '7e18b1d3-f219-4b2b-8afc-a3a7280fec54');


--
-- Data for Name: user_entity; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('95dcda34-2f55-4380-ac6d-f93310f1b321', NULL, 'ed8d050d-87fa-4236-bb4e-1060d7575ead', false, true, NULL, NULL, NULL, '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'kc_bootstrap_admin', 1776066221737, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('8387b32f-8c69-4bfe-af70-c2e7d3ab1f8a', 'superadmin@local.invalid', 'superadmin@local.invalid', true, true, NULL, 'Bootstrap', 'Superadmin', '6b03f9aa-9012-46b3-a691-480d464101db', 'superadmin', 1776066274924, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('b70b54cf-97a6-46c5-aebc-970dfcf0f928', 'hijewop375@iapapi.com', 'hijewop375@iapapi.com', true, true, NULL, 'Андрей', 'Иванов', '6b03f9aa-9012-46b3-a691-480d464101db', 'lead_economist', 1777965206999, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('8c72e4b5-3f3e-4ea0-aec2-036482068f8c', 'ngrakhova@vk.com', 'ngrakhova@vk.com', true, true, NULL, 'Анастасия', 'Грахова', '6b03f9aa-9012-46b3-a691-480d464101db', 'ip_grahova_anastasiya_andreevna_23_04', 1776956096220, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('39ecb97c-14f2-43c9-98c3-a1c40fe6685d', 'alexandrasmirnova230903@gmail.com', 'alexandrasmirnova230903@gmail.com', true, true, NULL, 'Руководитель', 'Проекта', '6b03f9aa-9012-46b3-a691-480d464101db', 'project_manager', 1777016555537, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('e9e4fb07-0e48-4f22-a6a3-b35b58867790', 'danilka@gmail.com', 'danilka@gmail.com', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'danilka', 1776952982700, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('aec8c936-b373-418e-b8d1-881816ea4d6e', 'latypov_20200@mail.ru', 'latypov_20200@mail.ru', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'danilkaa', 1776953121379, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('a83f5fc4-854f-474c-8bec-987472947829', 'annaosipova567@gmail.com', 'annaosipova567@gmail.com', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'baklazhka_23_04', 1776953323874, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('494b0122-d3b6-4ebb-9cfc-562171927895', 'latypov_2020@mail.ru', 'latypov_2020@mail.ru', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'feermoshkin', 1776955786952, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('1b3d4a9f-286a-4a24-bc61-8d108056a8f5', 'ffermoshkin@mail.ru', 'ffermoshkin@mail.ru', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'ffermoshkin', 1776955865661, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('2310266d-d483-463d-a2e5-848730825fde', 'angrakhova@alabuga.com', 'angrakhova@alabuga.com', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'angrakhova', 1776955931588, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('f008897a-c12a-45ee-943d-2effec955a51', 'zvezda.smerti148+rp_e2e@gmail.com', 'zvezda.smerti148+rp_e2e@gmail.com', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'auto_rp_e2e_20260424', 1777038296469, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('01392bd1-15c8-4493-9a27-762dbbd988e1', 'zvezda.smerti148+ve_e2e@gmail.com', 'zvezda.smerti148+ve_e2e@gmail.com', false, true, NULL, NULL, NULL, '6b03f9aa-9012-46b3-a691-480d464101db', 'auto_ve_e2e_20260424', 1777038431453, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('c3a9f123-fa66-4491-9e63-8e14b7b86653', 'sin.svaroga@mail.ru', 'sin.svaroga@mail.ru', true, true, NULL, 'ddddd', 'ddddd', '6b03f9aa-9012-46b3-a691-480d464101db', 'vvv', 1777296392077, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('cbce803f-4227-4c08-99dc-66dacc43cfae', 'zvezda.smerti148@gmail.com', 'zvezda.smerti148@gmail.com', true, true, NULL, 'Zvezda', 'Smerti', '6b03f9aa-9012-46b3-a691-480d464101db', 'auto_ek_e2e_20260424', 1777296560449, NULL, 0);
INSERT INTO keycloak.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) VALUES ('3bb41863-a1b5-43ef-afa0-5fcc60705a0a', 'sas6022693@gmail.com', 'sas6022693@gmail.com', true, true, NULL, 'Александра', 'Смирнова', '6b03f9aa-9012-46b3-a691-480d464101db', 'asmirnova_contragent', 1777298405547, NULL, 0);


--
-- Data for Name: credential; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('828ae535-a5e3-4491-8a6f-87574353e546', NULL, 'password', '95dcda34-2f55-4380-ac6d-f93310f1b321', 1776066221969, NULL, '{"value":"47x5CCQr7AfewD9wPxUyj6kTW04mBIx4qnX8eZFcCz8=","salt":"OBLrGY0rGHYbOcV2RuFDTQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('46caaaa0-37b3-45aa-a300-6319fd171f39', NULL, 'password', 'cbce803f-4227-4c08-99dc-66dacc43cfae', 1777296896998, NULL, '{"value":"uFlg36OPqd3kyHlStReX5r8/GfUe2BoDlOapTcqtuuw=","salt":"hDPwFqBSVGkQSYSWAiolwA==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 2);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('f725f797-312e-4574-9bde-0a083a0fe215', NULL, 'password', 'e9e4fb07-0e48-4f22-a6a3-b35b58867790', 1776952982816, NULL, '{"value":"vQX/ihmeirXEaOZ4+j4F7oVT/hCx5YMiM1Iqe5cTN3c=","salt":"a5qhlJluQH8WjDqtGAeMpQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('f6e23826-4730-4faa-8707-c966463c8691', NULL, 'password', 'aec8c936-b373-418e-b8d1-881816ea4d6e', 1776953121470, NULL, '{"value":"rTpun+rbpeGhkMwYhZWaKQaGl9Orp5sdA405sDhtpnk=","salt":"C1OaEa77kvRhPBC04g5AsQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('9ca45653-40dc-4a73-9a5f-b369ff83f371', NULL, 'password', '494b0122-d3b6-4ebb-9cfc-562171927895', 1776955787075, NULL, '{"value":"gnG+jcF2tMm8+mmhD/WTiDo1EvUi0LneJ/A8UdoV7fM=","salt":"VLON1DiXYTJbx05EnQvqsQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('7c511071-b2fc-4bd7-afd6-3c12aef321ca', NULL, 'password', '1b3d4a9f-286a-4a24-bc61-8d108056a8f5', 1776955865841, NULL, '{"value":"NDlXTDTAsYrnEbR07ZZJsaxWA/ArCNUsOCursk0oqYw=","salt":"ITOj1NH8Eq1FH/kosq94Vw==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('22144999-ff64-424d-9308-9659c7de0a5c', NULL, 'password', '2310266d-d483-463d-a2e5-848730825fde', 1776955931740, NULL, '{"value":"ezr7Nw7zma3aVOeKqvec1SY09qf2tuEa03qlCjc2zq0=","salt":"eu4GFR885BbGr/86w2Iemg==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('67fed36f-8aad-401f-91f4-1b6e12d62df4', NULL, 'password', '3bb41863-a1b5-43ef-afa0-5fcc60705a0a', 1777298405610, NULL, '{"value":"ybVSEu0dPA2zfOuDZhOnYJWzcacp+dSMy9Ma0K0CluY=","salt":"uxMIyXaNbePxbGnULi6UCw==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('4499d918-ff5b-4405-953f-695f950322aa', NULL, 'password', '8c72e4b5-3f3e-4ea0-aec2-036482068f8c', 1776956209282, NULL, '{"value":"RJnLZ4EZwKbNKXtWqh/mBmw+ANWOM5XB6iPPsMHHqPk=","salt":"BMpRLeVsUa8mdvy4wDELkg==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('c085d59a-f688-44bc-a5f0-11f81072a943', NULL, 'password', '39ecb97c-14f2-43c9-98c3-a1c40fe6685d', 1777016555629, NULL, '{"value":"bJrFoWazFwCUG4pZ9LxBZdTrnLPrU5T5+mIP9EX+AjI=","salt":"pcYJoMro8iU3n8S3fkVZMg==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('a2c93749-d8e7-4895-b691-21920a679335', NULL, 'password', 'f008897a-c12a-45ee-943d-2effec955a51', 1777038296613, NULL, '{"value":"yc3PQMFX05YqfDvUJWMgV5G30ubP0nYkkr+rIqNHVS8=","salt":"ZXZ1KxizbFMwRDEpqgCqQw==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('f5ced34b-6578-4235-b2f1-7ad70e39c460', NULL, 'password', '01392bd1-15c8-4493-9a27-762dbbd988e1', 1777038431636, NULL, '{"value":"gxZqmQpkI2m53mDXAteYhoRe7o5p52BHFmFUeTIf03k=","salt":"rHm4kiDD6NEY9XhAJqS85Q==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('6aa3721c-e5c6-4c6b-8037-edfd9bfcda47', NULL, 'password', 'c3a9f123-fa66-4491-9e63-8e14b7b86653', 1777296392184, NULL, '{"value":"6VGiKBRQaL7EfCUay7F+06p8uTHiil9HHpRrSGolpGY=","salt":"KfTsKMkyRyeGejjg1YWiUg==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('f0ec2367-4056-4869-bbde-9a39e74ec124', NULL, 'password', '8387b32f-8c69-4bfe-af70-c2e7d3ab1f8a', 1777964838822, NULL, '{"value":"Vxof0CvlPHxuXKSNb19pCe80dNdxTNjspAonWNzrFkA=","salt":"HKYdoQVn9h4BVrSAoQl2aQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 18);
INSERT INTO keycloak.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority, version) VALUES ('8b3861df-93db-4397-a046-6ff7780d24bc', NULL, 'password', 'b70b54cf-97a6-46c5-aebc-970dfcf0f928', 1777965265965, NULL, '{"value":"LUfha1tBGKaSXcD4xv142XMi71X1OUupg09ekxU3JH4=","salt":"BT2blhWqKQk/XY3vgdXRmQ==","additionalParameters":{}}', '{"hashIterations":5,"algorithm":"argon2","additionalParameters":{"hashLength":["32"],"memory":["7168"],"type":["id"],"version":["1.3"],"parallelism":["1"]}}', 10, 0);


--
-- Data for Name: databasechangelog; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.0.0.Final-KEYCLOAK-5461', 'sthorger@redhat.com', 'META-INF/jpa-changelog-1.0.0.Final.xml', '2026-04-13 07:43:16.545228', 1, 'EXECUTED', '9:6f1016664e21e16d26517a4418f5e3df', 'createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.0.0.Final-KEYCLOAK-5461', 'sthorger@redhat.com', 'META-INF/db2-jpa-changelog-1.0.0.Final.xml', '2026-04-13 07:43:16.645922', 2, 'MARK_RAN', '9:828775b1596a07d1200ba1d49e5e3941', 'createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.1.0.Beta1', 'sthorger@redhat.com', 'META-INF/jpa-changelog-1.1.0.Beta1.xml', '2026-04-13 07:43:16.726591', 3, 'EXECUTED', '9:5f090e44a7d595883c1fb61f4b41fd38', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=CLIENT_ATTRIBUTES; createTable tableName=CLIENT_SESSION_NOTE; createTable tableName=APP_NODE_REGISTRATIONS; addColumn table...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.1.0.Final', 'sthorger@redhat.com', 'META-INF/jpa-changelog-1.1.0.Final.xml', '2026-04-13 07:43:16.734885', 4, 'EXECUTED', '9:c07e577387a3d2c04d1adc9aaad8730e', 'renameColumn newColumnName=EVENT_TIME, oldColumnName=TIME, tableName=EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.2.0.Beta1', 'psilva@redhat.com', 'META-INF/jpa-changelog-1.2.0.Beta1.xml', '2026-04-13 07:43:16.956966', 5, 'EXECUTED', '9:b68ce996c655922dbcd2fe6b6ae72686', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.2.0.Beta1', 'psilva@redhat.com', 'META-INF/db2-jpa-changelog-1.2.0.Beta1.xml', '2026-04-13 07:43:17.002251', 6, 'MARK_RAN', '9:543b5c9989f024fe35c6f6c5a97de88e', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.2.0.RC1', 'bburke@redhat.com', 'META-INF/jpa-changelog-1.2.0.CR1.xml', '2026-04-13 07:43:17.210216', 7, 'EXECUTED', '9:765afebbe21cf5bbca048e632df38336', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.2.0.RC1', 'bburke@redhat.com', 'META-INF/db2-jpa-changelog-1.2.0.CR1.xml', '2026-04-13 07:43:17.228837', 8, 'MARK_RAN', '9:db4a145ba11a6fdaefb397f6dbf829a1', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.2.0.Final', 'keycloak', 'META-INF/jpa-changelog-1.2.0.Final.xml', '2026-04-13 07:43:17.260527', 9, 'EXECUTED', '9:9d05c7be10cdb873f8bcb41bc3a8ab23', 'update tableName=CLIENT; update tableName=CLIENT; update tableName=CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.3.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-1.3.0.xml', '2026-04-13 07:43:17.459944', 10, 'EXECUTED', '9:18593702353128d53111f9b1ff0b82b8', 'delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=ADMI...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.4.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-1.4.0.xml', '2026-04-13 07:43:17.572734', 11, 'EXECUTED', '9:6122efe5f090e41a85c0f1c9e52cbb62', 'delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.4.0', 'bburke@redhat.com', 'META-INF/db2-jpa-changelog-1.4.0.xml', '2026-04-13 07:43:17.58383', 12, 'MARK_RAN', '9:e1ff28bf7568451453f844c5d54bb0b5', 'delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.5.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-1.5.0.xml', '2026-04-13 07:43:17.627476', 13, 'EXECUTED', '9:7af32cd8957fbc069f796b61217483fd', 'delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.6.1_from15', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.6.1.xml', '2026-04-13 07:43:17.666243', 14, 'EXECUTED', '9:6005e15e84714cd83226bf7879f54190', 'addColumn tableName=REALM; addColumn tableName=KEYCLOAK_ROLE; addColumn tableName=CLIENT; createTable tableName=OFFLINE_USER_SESSION; createTable tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_US_SES_PK2, tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.6.1_from16-pre', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.6.1.xml', '2026-04-13 07:43:17.671612', 15, 'MARK_RAN', '9:bf656f5a2b055d07f314431cae76f06c', 'delete tableName=OFFLINE_CLIENT_SESSION; delete tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.6.1_from16', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.6.1.xml', '2026-04-13 07:43:17.680216', 16, 'MARK_RAN', '9:f8dadc9284440469dcf71e25ca6ab99b', 'dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_US_SES_PK, tableName=OFFLINE_USER_SESSION; dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_CL_SES_PK, tableName=OFFLINE_CLIENT_SESSION; addColumn tableName=OFFLINE_USER_SESSION; update tableName=OF...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.6.1', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.6.1.xml', '2026-04-13 07:43:17.688813', 17, 'EXECUTED', '9:d41d8cd98f00b204e9800998ecf8427e', 'empty', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.7.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-1.7.0.xml', '2026-04-13 07:43:17.802846', 18, 'EXECUTED', '9:3368ff0be4c2855ee2dd9ca813b38d8e', 'createTable tableName=KEYCLOAK_GROUP; createTable tableName=GROUP_ROLE_MAPPING; createTable tableName=GROUP_ATTRIBUTE; createTable tableName=USER_GROUP_MEMBERSHIP; createTable tableName=REALM_DEFAULT_GROUPS; addColumn tableName=IDENTITY_PROVIDER; ...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.8.0', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.8.0.xml', '2026-04-13 07:43:17.883962', 19, 'EXECUTED', '9:8ac2fb5dd030b24c0570a763ed75ed20', 'addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.8.0-2', 'keycloak', 'META-INF/jpa-changelog-1.8.0.xml', '2026-04-13 07:43:17.893229', 20, 'EXECUTED', '9:f91ddca9b19743db60e3057679810e6c', 'dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('22.0.5-24031', 'keycloak', 'META-INF/jpa-changelog-22.0.0.xml', '2026-04-13 07:43:28.723202', 119, 'MARK_RAN', '9:a60d2d7b315ec2d3eba9e2f145f9df28', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.8.0', 'mposolda@redhat.com', 'META-INF/db2-jpa-changelog-1.8.0.xml', '2026-04-13 07:43:17.901043', 21, 'MARK_RAN', '9:831e82914316dc8a57dc09d755f23c51', 'addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.8.0-2', 'keycloak', 'META-INF/db2-jpa-changelog-1.8.0.xml', '2026-04-13 07:43:17.906043', 22, 'MARK_RAN', '9:f91ddca9b19743db60e3057679810e6c', 'dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.9.0', 'mposolda@redhat.com', 'META-INF/jpa-changelog-1.9.0.xml', '2026-04-13 07:43:18.073687', 23, 'EXECUTED', '9:bc3d0f9e823a69dc21e23e94c7a94bb1', 'update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=REALM; update tableName=REALM; customChange; dr...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.9.1', 'keycloak', 'META-INF/jpa-changelog-1.9.1.xml', '2026-04-13 07:43:18.104689', 24, 'EXECUTED', '9:c9999da42f543575ab790e76439a2679', 'modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=PUBLIC_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.9.1', 'keycloak', 'META-INF/db2-jpa-changelog-1.9.1.xml', '2026-04-13 07:43:18.112893', 25, 'MARK_RAN', '9:0d6c65c6f58732d81569e77b10ba301d', 'modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('1.9.2', 'keycloak', 'META-INF/jpa-changelog-1.9.2.xml', '2026-04-13 07:43:19.177177', 26, 'EXECUTED', '9:fc576660fc016ae53d2d4778d84d86d0', 'createIndex indexName=IDX_USER_EMAIL, tableName=USER_ENTITY; createIndex indexName=IDX_USER_ROLE_MAPPING, tableName=USER_ROLE_MAPPING; createIndex indexName=IDX_USER_GROUP_MAPPING, tableName=USER_GROUP_MEMBERSHIP; createIndex indexName=IDX_USER_CO...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-2.0.0', 'psilva@redhat.com', 'META-INF/jpa-changelog-authz-2.0.0.xml', '2026-04-13 07:43:19.370904', 27, 'EXECUTED', '9:43ed6b0da89ff77206289e87eaa9c024', 'createTable tableName=RESOURCE_SERVER; addPrimaryKey constraintName=CONSTRAINT_FARS, tableName=RESOURCE_SERVER; addUniqueConstraint constraintName=UK_AU8TT6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER; createTable tableName=RESOURCE_SERVER_RESOU...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-2.5.1', 'psilva@redhat.com', 'META-INF/jpa-changelog-authz-2.5.1.xml', '2026-04-13 07:43:19.38136', 28, 'EXECUTED', '9:44bae577f551b3738740281eceb4ea70', 'update tableName=RESOURCE_SERVER_POLICY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.1.0-KEYCLOAK-5461', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.1.0.xml', '2026-04-13 07:43:19.467249', 29, 'EXECUTED', '9:bd88e1f833df0420b01e114533aee5e8', 'createTable tableName=BROKER_LINK; createTable tableName=FED_USER_ATTRIBUTE; createTable tableName=FED_USER_CONSENT; createTable tableName=FED_USER_CONSENT_ROLE; createTable tableName=FED_USER_CONSENT_PROT_MAPPER; createTable tableName=FED_USER_CR...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.2.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.2.0.xml', '2026-04-13 07:43:19.508456', 30, 'EXECUTED', '9:a7022af5267f019d020edfe316ef4371', 'addColumn tableName=ADMIN_EVENT_ENTITY; createTable tableName=CREDENTIAL_ATTRIBUTE; createTable tableName=FED_CREDENTIAL_ATTRIBUTE; modifyDataType columnName=VALUE, tableName=CREDENTIAL; addForeignKeyConstraint baseTableName=FED_CREDENTIAL_ATTRIBU...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.3.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.3.0.xml', '2026-04-13 07:43:19.559488', 31, 'EXECUTED', '9:fc155c394040654d6a79227e56f5e25a', 'createTable tableName=FEDERATED_USER; addPrimaryKey constraintName=CONSTR_FEDERATED_USER, tableName=FEDERATED_USER; dropDefaultValue columnName=TOTP, tableName=USER_ENTITY; dropColumn columnName=TOTP, tableName=USER_ENTITY; addColumn tableName=IDE...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.4.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.4.0.xml', '2026-04-13 07:43:19.576184', 32, 'EXECUTED', '9:eac4ffb2a14795e5dc7b426063e54d88', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.5.0.xml', '2026-04-13 07:43:19.586129', 33, 'EXECUTED', '9:54937c05672568c4c64fc9524c1e9462', 'customChange; modifyDataType columnName=USER_ID, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.0-unicode-oracle', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-2.5.0.xml', '2026-04-13 07:43:19.590365', 34, 'MARK_RAN', '9:737ee933fd399814ed5e24f3b1bbe39d', 'modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.0-unicode-other-dbs', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-2.5.0.xml', '2026-04-13 07:43:19.639974', 35, 'EXECUTED', '9:33d72168746f81f98ae3a1e8e0ca3554', 'modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.0-duplicate-email-support', 'slawomir@dabek.name', 'META-INF/jpa-changelog-2.5.0.xml', '2026-04-13 07:43:19.661006', 36, 'EXECUTED', '9:61b6d3d7a4c0e0024b0c839da283da0c', 'addColumn tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.0-unique-group-names', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-2.5.0.xml', '2026-04-13 07:43:19.672896', 37, 'EXECUTED', '9:8dcac7bdf7378e7d823cdfddebf72fda', 'addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('2.5.1', 'bburke@redhat.com', 'META-INF/jpa-changelog-2.5.1.xml', '2026-04-13 07:43:19.678817', 38, 'EXECUTED', '9:a2b870802540cb3faa72098db5388af3', 'addColumn tableName=FED_USER_CONSENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.0.0', 'bburke@redhat.com', 'META-INF/jpa-changelog-3.0.0.xml', '2026-04-13 07:43:19.684875', 39, 'EXECUTED', '9:132a67499ba24bcc54fb5cbdcfe7e4c0', 'addColumn tableName=IDENTITY_PROVIDER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.2.0-fix', 'keycloak', 'META-INF/jpa-changelog-3.2.0.xml', '2026-04-13 07:43:19.686729', 40, 'MARK_RAN', '9:938f894c032f5430f2b0fafb1a243462', 'addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.2.0-fix-with-keycloak-5416', 'keycloak', 'META-INF/jpa-changelog-3.2.0.xml', '2026-04-13 07:43:19.692119', 41, 'MARK_RAN', '9:845c332ff1874dc5d35974b0babf3006', 'dropIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS; addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS; createIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.2.0-fix-offline-sessions', 'hmlnarik', 'META-INF/jpa-changelog-3.2.0.xml', '2026-04-13 07:43:19.702856', 42, 'EXECUTED', '9:fc86359c079781adc577c5a217e4d04c', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.2.0-fixed', 'keycloak', 'META-INF/jpa-changelog-3.2.0.xml', '2026-04-13 07:43:23.783096', 43, 'EXECUTED', '9:59a64800e3c0d09b825f8a3b444fa8f4', 'addColumn tableName=REALM; dropPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_PK2, tableName=OFFLINE_CLIENT_SESSION; dropColumn columnName=CLIENT_SESSION_ID, tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_P...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.3.0', 'keycloak', 'META-INF/jpa-changelog-3.3.0.xml', '2026-04-13 07:43:23.79808', 44, 'EXECUTED', '9:d48d6da5c6ccf667807f633fe489ce88', 'addColumn tableName=USER_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-3.4.0.CR1-resource-server-pk-change-part1', 'glavoie@gmail.com', 'META-INF/jpa-changelog-authz-3.4.0.CR1.xml', '2026-04-13 07:43:23.810404', 45, 'EXECUTED', '9:dde36f7973e80d71fceee683bc5d2951', 'addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_RESOURCE; addColumn tableName=RESOURCE_SERVER_SCOPE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-3.4.0.CR1-resource-server-pk-change-part2-KEYCLOAK-6095', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-authz-3.4.0.CR1.xml', '2026-04-13 07:43:23.835218', 46, 'EXECUTED', '9:b855e9b0a406b34fa323235a0cf4f640', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-3.4.0.CR1-resource-server-pk-change-part3-fixed', 'glavoie@gmail.com', 'META-INF/jpa-changelog-authz-3.4.0.CR1.xml', '2026-04-13 07:43:23.841288', 47, 'MARK_RAN', '9:51abbacd7b416c50c4421a8cabf7927e', 'dropIndex indexName=IDX_RES_SERV_POL_RES_SERV, tableName=RESOURCE_SERVER_POLICY; dropIndex indexName=IDX_RES_SRV_RES_RES_SRV, tableName=RESOURCE_SERVER_RESOURCE; dropIndex indexName=IDX_RES_SRV_SCOPE_RES_SRV, tableName=RESOURCE_SERVER_SCOPE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-3.4.0.CR1-resource-server-pk-change-part3-fixed-nodropindex', 'glavoie@gmail.com', 'META-INF/jpa-changelog-authz-3.4.0.CR1.xml', '2026-04-13 07:43:24.280149', 48, 'EXECUTED', '9:bdc99e567b3398bac83263d375aad143', 'addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_POLICY; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_RESOURCE; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, ...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authn-3.4.0.CR1-refresh-token-max-reuse', 'glavoie@gmail.com', 'META-INF/jpa-changelog-authz-3.4.0.CR1.xml', '2026-04-13 07:43:24.296307', 49, 'EXECUTED', '9:d198654156881c46bfba39abd7769e69', 'addColumn tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.4.0', 'keycloak', 'META-INF/jpa-changelog-3.4.0.xml', '2026-04-13 07:43:24.345691', 50, 'EXECUTED', '9:cfdd8736332ccdd72c5256ccb42335db', 'addPrimaryKey constraintName=CONSTRAINT_REALM_DEFAULT_ROLES, tableName=REALM_DEFAULT_ROLES; addPrimaryKey constraintName=CONSTRAINT_COMPOSITE_ROLE, tableName=COMPOSITE_ROLE; addPrimaryKey constraintName=CONSTR_REALM_DEFAULT_GROUPS, tableName=REALM...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.4.0-KEYCLOAK-5230', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-3.4.0.xml', '2026-04-13 07:43:25.407252', 51, 'EXECUTED', '9:7c84de3d9bd84d7f077607c1a4dcb714', 'createIndex indexName=IDX_FU_ATTRIBUTE, tableName=FED_USER_ATTRIBUTE; createIndex indexName=IDX_FU_CONSENT, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CONSENT_RU, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CREDENTIAL, t...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.4.1', 'psilva@redhat.com', 'META-INF/jpa-changelog-3.4.1.xml', '2026-04-13 07:43:25.414796', 52, 'EXECUTED', '9:5a6bb36cbefb6a9d6928452c0852af2d', 'modifyDataType columnName=VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.4.2', 'keycloak', 'META-INF/jpa-changelog-3.4.2.xml', '2026-04-13 07:43:25.483444', 53, 'EXECUTED', '9:8f23e334dbc59f82e0a328373ca6ced0', 'update tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('3.4.2-KEYCLOAK-5172', 'mkanis@redhat.com', 'META-INF/jpa-changelog-3.4.2.xml', '2026-04-13 07:43:25.4972', 54, 'EXECUTED', '9:9156214268f09d970cdf0e1564d866af', 'update tableName=CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.0.0-KEYCLOAK-6335', 'bburke@redhat.com', 'META-INF/jpa-changelog-4.0.0.xml', '2026-04-13 07:43:25.525513', 55, 'EXECUTED', '9:db806613b1ed154826c02610b7dbdf74', 'createTable tableName=CLIENT_AUTH_FLOW_BINDINGS; addPrimaryKey constraintName=C_CLI_FLOW_BIND, tableName=CLIENT_AUTH_FLOW_BINDINGS', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.0.0-CLEANUP-UNUSED-TABLE', 'bburke@redhat.com', 'META-INF/jpa-changelog-4.0.0.xml', '2026-04-13 07:43:25.543532', 56, 'EXECUTED', '9:229a041fb72d5beac76bb94a5fa709de', 'dropTable tableName=CLIENT_IDENTITY_PROV_MAPPING', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.0.0-KEYCLOAK-6228', 'bburke@redhat.com', 'META-INF/jpa-changelog-4.0.0.xml', '2026-04-13 07:43:25.670095', 57, 'EXECUTED', '9:079899dade9c1e683f26b2aa9ca6ff04', 'dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; dropNotNullConstraint columnName=CLIENT_ID, tableName=USER_CONSENT; addColumn tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHO...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.0.0-KEYCLOAK-5579-fixed', 'mposolda@redhat.com', 'META-INF/jpa-changelog-4.0.0.xml', '2026-04-13 07:43:26.594612', 58, 'EXECUTED', '9:139b79bcbbfe903bb1c2d2a4dbf001d9', 'dropForeignKeyConstraint baseTableName=CLIENT_TEMPLATE_ATTRIBUTES, constraintName=FK_CL_TEMPL_ATTR_TEMPL; renameTable newTableName=CLIENT_SCOPE_ATTRIBUTES, oldTableName=CLIENT_TEMPLATE_ATTRIBUTES; renameColumn newColumnName=SCOPE_ID, oldColumnName...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-4.0.0.CR1', 'psilva@redhat.com', 'META-INF/jpa-changelog-authz-4.0.0.CR1.xml', '2026-04-13 07:43:26.844631', 59, 'EXECUTED', '9:b55738ad889860c625ba2bf483495a04', 'createTable tableName=RESOURCE_SERVER_PERM_TICKET; addPrimaryKey constraintName=CONSTRAINT_FAPMT, tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRHO213XCX4WNKOG82SSPMT...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-4.0.0.Beta3', 'psilva@redhat.com', 'META-INF/jpa-changelog-authz-4.0.0.Beta3.xml', '2026-04-13 07:43:26.852587', 60, 'EXECUTED', '9:e0057eac39aa8fc8e09ac6cfa4ae15fe', 'addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRPO2128CX4WNKOG82SSRFY, referencedTableName=RESOURCE_SERVER_POLICY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-4.2.0.Final', 'mhajas@redhat.com', 'META-INF/jpa-changelog-authz-4.2.0.Final.xml', '2026-04-13 07:43:26.863767', 61, 'EXECUTED', '9:42a33806f3a0443fe0e7feeec821326c', 'createTable tableName=RESOURCE_URIS; addForeignKeyConstraint baseTableName=RESOURCE_URIS, constraintName=FK_RESOURCE_SERVER_URIS, referencedTableName=RESOURCE_SERVER_RESOURCE; customChange; dropColumn columnName=URI, tableName=RESOURCE_SERVER_RESO...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-4.2.0.Final-KEYCLOAK-9944', 'hmlnarik@redhat.com', 'META-INF/jpa-changelog-authz-4.2.0.Final.xml', '2026-04-13 07:43:26.869654', 62, 'EXECUTED', '9:9968206fca46eecc1f51db9c024bfe56', 'addPrimaryKey constraintName=CONSTRAINT_RESOUR_URIS_PK, tableName=RESOURCE_URIS', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.2.0-KEYCLOAK-6313', 'wadahiro@gmail.com', 'META-INF/jpa-changelog-4.2.0.xml', '2026-04-13 07:43:26.876738', 63, 'EXECUTED', '9:92143a6daea0a3f3b8f598c97ce55c3d', 'addColumn tableName=REQUIRED_ACTION_PROVIDER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.3.0-KEYCLOAK-7984', 'wadahiro@gmail.com', 'META-INF/jpa-changelog-4.3.0.xml', '2026-04-13 07:43:26.882821', 64, 'EXECUTED', '9:82bab26a27195d889fb0429003b18f40', 'update tableName=REQUIRED_ACTION_PROVIDER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.6.0-KEYCLOAK-7950', 'psilva@redhat.com', 'META-INF/jpa-changelog-4.6.0.xml', '2026-04-13 07:43:26.895684', 65, 'EXECUTED', '9:e590c88ddc0b38b0ae4249bbfcb5abc3', 'update tableName=RESOURCE_SERVER_RESOURCE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.6.0-KEYCLOAK-8377', 'keycloak', 'META-INF/jpa-changelog-4.6.0.xml', '2026-04-13 07:43:27.154038', 66, 'EXECUTED', '9:5c1f475536118dbdc38d5d7977950cc0', 'createTable tableName=ROLE_ATTRIBUTE; addPrimaryKey constraintName=CONSTRAINT_ROLE_ATTRIBUTE_PK, tableName=ROLE_ATTRIBUTE; addForeignKeyConstraint baseTableName=ROLE_ATTRIBUTE, constraintName=FK_ROLE_ATTRIBUTE_ID, referencedTableName=KEYCLOAK_ROLE...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.6.0-KEYCLOAK-8555', 'gideonray@gmail.com', 'META-INF/jpa-changelog-4.6.0.xml', '2026-04-13 07:43:27.311553', 67, 'EXECUTED', '9:e7c9f5f9c4d67ccbbcc215440c718a17', 'createIndex indexName=IDX_COMPONENT_PROVIDER_TYPE, tableName=COMPONENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.7.0-KEYCLOAK-1267', 'sguilhen@redhat.com', 'META-INF/jpa-changelog-4.7.0.xml', '2026-04-13 07:43:27.31922', 68, 'EXECUTED', '9:88e0bfdda924690d6f4e430c53447dd5', 'addColumn tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.7.0-KEYCLOAK-7275', 'keycloak', 'META-INF/jpa-changelog-4.7.0.xml', '2026-04-13 07:43:27.368611', 69, 'EXECUTED', '9:f53177f137e1c46b6a88c59ec1cb5218', 'renameColumn newColumnName=CREATED_ON, oldColumnName=LAST_SESSION_REFRESH, tableName=OFFLINE_USER_SESSION; addNotNullConstraint columnName=CREATED_ON, tableName=OFFLINE_USER_SESSION; addColumn tableName=OFFLINE_USER_SESSION; customChange; createIn...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('4.8.0-KEYCLOAK-8835', 'sguilhen@redhat.com', 'META-INF/jpa-changelog-4.8.0.xml', '2026-04-13 07:43:27.380243', 70, 'EXECUTED', '9:a74d33da4dc42a37ec27121580d1459f', 'addNotNullConstraint columnName=SSO_MAX_LIFESPAN_REMEMBER_ME, tableName=REALM; addNotNullConstraint columnName=SSO_IDLE_TIMEOUT_REMEMBER_ME, tableName=REALM', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('authz-7.0.0-KEYCLOAK-10443', 'psilva@redhat.com', 'META-INF/jpa-changelog-authz-7.0.0.xml', '2026-04-13 07:43:27.388971', 71, 'EXECUTED', '9:fd4ade7b90c3b67fae0bfcfcb42dfb5f', 'addColumn tableName=RESOURCE_SERVER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('8.0.0-adding-credential-columns', 'keycloak', 'META-INF/jpa-changelog-8.0.0.xml', '2026-04-13 07:43:27.403969', 72, 'EXECUTED', '9:aa072ad090bbba210d8f18781b8cebf4', 'addColumn tableName=CREDENTIAL; addColumn tableName=FED_USER_CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('8.0.0-updating-credential-data-not-oracle-fixed', 'keycloak', 'META-INF/jpa-changelog-8.0.0.xml', '2026-04-13 07:43:27.417757', 73, 'EXECUTED', '9:1ae6be29bab7c2aa376f6983b932be37', 'update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('8.0.0-updating-credential-data-oracle-fixed', 'keycloak', 'META-INF/jpa-changelog-8.0.0.xml', '2026-04-13 07:43:27.422309', 74, 'MARK_RAN', '9:14706f286953fc9a25286dbd8fb30d97', 'update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('8.0.0-credential-cleanup-fixed', 'keycloak', 'META-INF/jpa-changelog-8.0.0.xml', '2026-04-13 07:43:27.45637', 75, 'EXECUTED', '9:2b9cc12779be32c5b40e2e67711a218b', 'dropDefaultValue columnName=COUNTER, tableName=CREDENTIAL; dropDefaultValue columnName=DIGITS, tableName=CREDENTIAL; dropDefaultValue columnName=PERIOD, tableName=CREDENTIAL; dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; dropColumn ...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('8.0.0-resource-tag-support', 'keycloak', 'META-INF/jpa-changelog-8.0.0.xml', '2026-04-13 07:43:27.536208', 76, 'EXECUTED', '9:91fa186ce7a5af127a2d7a91ee083cc5', 'addColumn tableName=MIGRATION_MODEL; createIndex indexName=IDX_UPDATE_TIME, tableName=MIGRATION_MODEL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.0-always-display-client', 'keycloak', 'META-INF/jpa-changelog-9.0.0.xml', '2026-04-13 07:43:27.542182', 77, 'EXECUTED', '9:6335e5c94e83a2639ccd68dd24e2e5ad', 'addColumn tableName=CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.0-drop-constraints-for-column-increase', 'keycloak', 'META-INF/jpa-changelog-9.0.0.xml', '2026-04-13 07:43:27.544839', 78, 'MARK_RAN', '9:6bdb5658951e028bfe16fa0a8228b530', 'dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5PMT, tableName=RESOURCE_SERVER_PERM_TICKET; dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER_RESOURCE; dropPrimaryKey constraintName=CONSTRAINT_O...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.0-increase-column-size-federated-fk', 'keycloak', 'META-INF/jpa-changelog-9.0.0.xml', '2026-04-13 07:43:27.58472', 79, 'EXECUTED', '9:d5bc15a64117ccad481ce8792d4c608f', 'modifyDataType columnName=CLIENT_ID, tableName=FED_USER_CONSENT; modifyDataType columnName=CLIENT_REALM_CONSTRAINT, tableName=KEYCLOAK_ROLE; modifyDataType columnName=OWNER, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=CLIENT_ID, ta...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.0-recreate-constraints-after-column-increase', 'keycloak', 'META-INF/jpa-changelog-9.0.0.xml', '2026-04-13 07:43:27.587585', 80, 'MARK_RAN', '9:077cba51999515f4d3e7ad5619ab592c', 'addNotNullConstraint columnName=CLIENT_ID, tableName=OFFLINE_CLIENT_SESSION; addNotNullConstraint columnName=OWNER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNullConstraint columnName=REQUESTER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNull...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.1-add-index-to-client.client_id', 'keycloak', 'META-INF/jpa-changelog-9.0.1.xml', '2026-04-13 07:43:27.661451', 81, 'EXECUTED', '9:be969f08a163bf47c6b9e9ead8ac2afb', 'createIndex indexName=IDX_CLIENT_ID, tableName=CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.1-KEYCLOAK-12579-drop-constraints', 'keycloak', 'META-INF/jpa-changelog-9.0.1.xml', '2026-04-13 07:43:27.663804', 82, 'MARK_RAN', '9:6d3bb4408ba5a72f39bd8a0b301ec6e3', 'dropUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.1-KEYCLOAK-12579-add-not-null-constraint', 'keycloak', 'META-INF/jpa-changelog-9.0.1.xml', '2026-04-13 07:43:27.670431', 83, 'EXECUTED', '9:966bda61e46bebf3cc39518fbed52fa7', 'addNotNullConstraint columnName=PARENT_GROUP, tableName=KEYCLOAK_GROUP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.1-KEYCLOAK-12579-recreate-constraints', 'keycloak', 'META-INF/jpa-changelog-9.0.1.xml', '2026-04-13 07:43:27.672683', 84, 'MARK_RAN', '9:8dcac7bdf7378e7d823cdfddebf72fda', 'addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('9.0.1-add-index-to-events', 'keycloak', 'META-INF/jpa-changelog-9.0.1.xml', '2026-04-13 07:43:27.721579', 85, 'EXECUTED', '9:7d93d602352a30c0c317e6a609b56599', 'createIndex indexName=IDX_EVENT_TIME, tableName=EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('map-remove-ri', 'keycloak', 'META-INF/jpa-changelog-11.0.0.xml', '2026-04-13 07:43:27.725227', 86, 'EXECUTED', '9:71c5969e6cdd8d7b6f47cebc86d37627', 'dropForeignKeyConstraint baseTableName=REALM, constraintName=FK_TRAF444KK6QRKMS7N56AIWQ5Y; dropForeignKeyConstraint baseTableName=KEYCLOAK_ROLE, constraintName=FK_KJHO5LE2C0RAL09FL8CM9WFW9', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('map-remove-ri', 'keycloak', 'META-INF/jpa-changelog-12.0.0.xml', '2026-04-13 07:43:27.732124', 87, 'EXECUTED', '9:a9ba7d47f065f041b7da856a81762021', 'dropForeignKeyConstraint baseTableName=REALM_DEFAULT_GROUPS, constraintName=FK_DEF_GROUPS_GROUP; dropForeignKeyConstraint baseTableName=REALM_DEFAULT_ROLES, constraintName=FK_H4WPD7W4HSOOLNI3H0SW7BTJE; dropForeignKeyConstraint baseTableName=CLIENT...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('12.1.0-add-realm-localization-table', 'keycloak', 'META-INF/jpa-changelog-12.0.0.xml', '2026-04-13 07:43:27.743217', 88, 'EXECUTED', '9:fffabce2bc01e1a8f5110d5278500065', 'createTable tableName=REALM_LOCALIZATIONS; addPrimaryKey tableName=REALM_LOCALIZATIONS', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('default-roles', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.749949', 89, 'EXECUTED', '9:fa8a5b5445e3857f4b010bafb5009957', 'addColumn tableName=REALM; customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('default-roles-cleanup', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.756218', 90, 'EXECUTED', '9:67ac3241df9a8582d591c5ed87125f39', 'dropTable tableName=REALM_DEFAULT_ROLES; dropTable tableName=CLIENT_DEFAULT_ROLES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('13.0.0-KEYCLOAK-16844', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.792794', 91, 'EXECUTED', '9:ad1194d66c937e3ffc82386c050ba089', 'createIndex indexName=IDX_OFFLINE_USS_PRELOAD, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('map-remove-ri-13.0.0', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.801817', 92, 'EXECUTED', '9:d9be619d94af5a2f5d07b9f003543b91', 'dropForeignKeyConstraint baseTableName=DEFAULT_CLIENT_SCOPE, constraintName=FK_R_DEF_CLI_SCOPE_SCOPE; dropForeignKeyConstraint baseTableName=CLIENT_SCOPE_CLIENT, constraintName=FK_C_CLI_SCOPE_SCOPE; dropForeignKeyConstraint baseTableName=CLIENT_SC...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('13.0.0-KEYCLOAK-17992-drop-constraints', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.803842', 93, 'MARK_RAN', '9:544d201116a0fcc5a5da0925fbbc3bde', 'dropPrimaryKey constraintName=C_CLI_SCOPE_BIND, tableName=CLIENT_SCOPE_CLIENT; dropIndex indexName=IDX_CLSCOPE_CL, tableName=CLIENT_SCOPE_CLIENT; dropIndex indexName=IDX_CL_CLSCOPE, tableName=CLIENT_SCOPE_CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('13.0.0-increase-column-size-federated', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.814301', 94, 'EXECUTED', '9:43c0c1055b6761b4b3e89de76d612ccf', 'modifyDataType columnName=CLIENT_ID, tableName=CLIENT_SCOPE_CLIENT; modifyDataType columnName=SCOPE_ID, tableName=CLIENT_SCOPE_CLIENT', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('13.0.0-KEYCLOAK-17992-recreate-constraints', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.816667', 95, 'MARK_RAN', '9:8bd711fd0330f4fe980494ca43ab1139', 'addNotNullConstraint columnName=CLIENT_ID, tableName=CLIENT_SCOPE_CLIENT; addNotNullConstraint columnName=SCOPE_ID, tableName=CLIENT_SCOPE_CLIENT; addPrimaryKey constraintName=C_CLI_SCOPE_BIND, tableName=CLIENT_SCOPE_CLIENT; createIndex indexName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('json-string-accomodation-fixed', 'keycloak', 'META-INF/jpa-changelog-13.0.0.xml', '2026-04-13 07:43:27.824998', 96, 'EXECUTED', '9:e07d2bc0970c348bb06fb63b1f82ddbf', 'addColumn tableName=REALM_ATTRIBUTE; update tableName=REALM_ATTRIBUTE; dropColumn columnName=VALUE, tableName=REALM_ATTRIBUTE; renameColumn newColumnName=VALUE, oldColumnName=VALUE_NEW, tableName=REALM_ATTRIBUTE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('14.0.0-KEYCLOAK-11019', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:27.966577', 97, 'EXECUTED', '9:24fb8611e97f29989bea412aa38d12b7', 'createIndex indexName=IDX_OFFLINE_CSS_PRELOAD, tableName=OFFLINE_CLIENT_SESSION; createIndex indexName=IDX_OFFLINE_USS_BY_USER, tableName=OFFLINE_USER_SESSION; createIndex indexName=IDX_OFFLINE_USS_BY_USERSESS, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('14.0.0-KEYCLOAK-18286', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:27.968888', 98, 'MARK_RAN', '9:259f89014ce2506ee84740cbf7163aa7', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('14.0.0-KEYCLOAK-18286-revert', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:27.99612', 99, 'MARK_RAN', '9:04baaf56c116ed19951cbc2cca584022', 'dropIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('14.0.0-KEYCLOAK-18286-supported-dbs', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:28.060074', 100, 'EXECUTED', '9:60ca84a0f8c94ec8c3504a5a3bc88ee8', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('14.0.0-KEYCLOAK-18286-unsupported-dbs', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:28.063779', 101, 'MARK_RAN', '9:d3d977031d431db16e2c181ce49d73e9', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('KEYCLOAK-17267-add-index-to-user-attributes', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:28.130211', 102, 'EXECUTED', '9:0b305d8d1277f3a89a0a53a659ad274c', 'createIndex indexName=IDX_USER_ATTRIBUTE_NAME, tableName=USER_ATTRIBUTE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('KEYCLOAK-18146-add-saml-art-binding-identifier', 'keycloak', 'META-INF/jpa-changelog-14.0.0.xml', '2026-04-13 07:43:28.139943', 103, 'EXECUTED', '9:2c374ad2cdfe20e2905a84c8fac48460', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('15.0.0-KEYCLOAK-18467', 'keycloak', 'META-INF/jpa-changelog-15.0.0.xml', '2026-04-13 07:43:28.15295', 104, 'EXECUTED', '9:47a760639ac597360a8219f5b768b4de', 'addColumn tableName=REALM_LOCALIZATIONS; update tableName=REALM_LOCALIZATIONS; dropColumn columnName=TEXTS, tableName=REALM_LOCALIZATIONS; renameColumn newColumnName=TEXTS, oldColumnName=TEXTS_NEW, tableName=REALM_LOCALIZATIONS; addNotNullConstrai...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('17.0.0-9562', 'keycloak', 'META-INF/jpa-changelog-17.0.0.xml', '2026-04-13 07:43:28.252054', 105, 'EXECUTED', '9:a6272f0576727dd8cad2522335f5d99e', 'createIndex indexName=IDX_USER_SERVICE_ACCOUNT, tableName=USER_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('18.0.0-10625-IDX_ADMIN_EVENT_TIME', 'keycloak', 'META-INF/jpa-changelog-18.0.0.xml', '2026-04-13 07:43:28.352012', 106, 'EXECUTED', '9:015479dbd691d9cc8669282f4828c41d', 'createIndex indexName=IDX_ADMIN_EVENT_TIME, tableName=ADMIN_EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('18.0.15-30992-index-consent', 'keycloak', 'META-INF/jpa-changelog-18.0.15.xml', '2026-04-13 07:43:28.439328', 107, 'EXECUTED', '9:80071ede7a05604b1f4906f3bf3b00f0', 'createIndex indexName=IDX_USCONSENT_SCOPE_ID, tableName=USER_CONSENT_CLIENT_SCOPE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('19.0.0-10135', 'keycloak', 'META-INF/jpa-changelog-19.0.0.xml', '2026-04-13 07:43:28.449784', 108, 'EXECUTED', '9:9518e495fdd22f78ad6425cc30630221', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('20.0.0-12964-supported-dbs', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.566304', 109, 'EXECUTED', '9:e5f243877199fd96bcc842f27a1656ac', 'createIndex indexName=IDX_GROUP_ATT_BY_NAME_VALUE, tableName=GROUP_ATTRIBUTE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('20.0.0-12964-supported-dbs-edb-migration', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.642877', 110, 'EXECUTED', '9:a6b18a8e38062df5793edbe064f4aecd', 'dropIndex indexName=IDX_GROUP_ATT_BY_NAME_VALUE, tableName=GROUP_ATTRIBUTE; createIndex indexName=IDX_GROUP_ATT_BY_NAME_VALUE, tableName=GROUP_ATTRIBUTE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('20.0.0-12964-unsupported-dbs', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.646136', 111, 'MARK_RAN', '9:1a6fcaa85e20bdeae0a9ce49b41946a5', 'createIndex indexName=IDX_GROUP_ATT_BY_NAME_VALUE, tableName=GROUP_ATTRIBUTE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('client-attributes-string-accomodation-fixed-pre-drop-index', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.652093', 112, 'EXECUTED', '9:04baaf56c116ed19951cbc2cca584022', 'dropIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('client-attributes-string-accomodation-fixed', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.66292', 113, 'EXECUTED', '9:3f332e13e90739ed0c35b0b25b7822ca', 'addColumn tableName=CLIENT_ATTRIBUTES; update tableName=CLIENT_ATTRIBUTES; dropColumn columnName=VALUE, tableName=CLIENT_ATTRIBUTES; renameColumn newColumnName=VALUE, oldColumnName=VALUE_NEW, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('client-attributes-string-accomodation-fixed-post-create-index', 'keycloak', 'META-INF/jpa-changelog-20.0.0.xml', '2026-04-13 07:43:28.665765', 114, 'MARK_RAN', '9:bd2bd0fc7768cf0845ac96a8786fa735', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('21.0.2-17277', 'keycloak', 'META-INF/jpa-changelog-21.0.2.xml', '2026-04-13 07:43:28.673135', 115, 'EXECUTED', '9:7ee1f7a3fb8f5588f171fb9a6ab623c0', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('21.1.0-19404', 'keycloak', 'META-INF/jpa-changelog-21.1.0.xml', '2026-04-13 07:43:28.706212', 116, 'EXECUTED', '9:3d7e830b52f33676b9d64f7f2b2ea634', 'modifyDataType columnName=DECISION_STRATEGY, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=LOGIC, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=POLICY_ENFORCE_MODE, tableName=RESOURCE_SERVER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('21.1.0-19404-2', 'keycloak', 'META-INF/jpa-changelog-21.1.0.xml', '2026-04-13 07:43:28.713383', 117, 'MARK_RAN', '9:627d032e3ef2c06c0e1f73d2ae25c26c', 'addColumn tableName=RESOURCE_SERVER_POLICY; update tableName=RESOURCE_SERVER_POLICY; dropColumn columnName=DECISION_STRATEGY, tableName=RESOURCE_SERVER_POLICY; renameColumn newColumnName=DECISION_STRATEGY, oldColumnName=DECISION_STRATEGY_NEW, tabl...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('22.0.0-17484-updated', 'keycloak', 'META-INF/jpa-changelog-22.0.0.xml', '2026-04-13 07:43:28.720179', 118, 'EXECUTED', '9:90af0bfd30cafc17b9f4d6eccd92b8b3', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('23.0.0-12062', 'keycloak', 'META-INF/jpa-changelog-23.0.0.xml', '2026-04-13 07:43:28.729816', 120, 'EXECUTED', '9:2168fbe728fec46ae9baf15bf80927b8', 'addColumn tableName=COMPONENT_CONFIG; update tableName=COMPONENT_CONFIG; dropColumn columnName=VALUE, tableName=COMPONENT_CONFIG; renameColumn newColumnName=VALUE, oldColumnName=VALUE_NEW, tableName=COMPONENT_CONFIG', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('23.0.0-17258', 'keycloak', 'META-INF/jpa-changelog-23.0.0.xml', '2026-04-13 07:43:28.734667', 121, 'EXECUTED', '9:36506d679a83bbfda85a27ea1864dca8', 'addColumn tableName=EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.0-9758', 'keycloak', 'META-INF/jpa-changelog-24.0.0.xml', '2026-04-13 07:43:29.009391', 122, 'EXECUTED', '9:502c557a5189f600f0f445a9b49ebbce', 'addColumn tableName=USER_ATTRIBUTE; addColumn tableName=FED_USER_ATTRIBUTE; createIndex indexName=USER_ATTR_LONG_VALUES, tableName=USER_ATTRIBUTE; createIndex indexName=FED_USER_ATTR_LONG_VALUES, tableName=FED_USER_ATTRIBUTE; createIndex indexName...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.0-9758-2', 'keycloak', 'META-INF/jpa-changelog-24.0.0.xml', '2026-04-13 07:43:29.024473', 123, 'EXECUTED', '9:bf0fdee10afdf597a987adbf291db7b2', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.0-26618-drop-index-if-present', 'keycloak', 'META-INF/jpa-changelog-24.0.0.xml', '2026-04-13 07:43:29.03533', 124, 'MARK_RAN', '9:04baaf56c116ed19951cbc2cca584022', 'dropIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.0-26618-reindex', 'keycloak', 'META-INF/jpa-changelog-24.0.0.xml', '2026-04-13 07:43:29.109817', 125, 'EXECUTED', '9:08707c0f0db1cef6b352db03a60edc7f', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.0-26618-edb-migration', 'keycloak', 'META-INF/jpa-changelog-24.0.0.xml', '2026-04-13 07:43:29.224386', 126, 'EXECUTED', '9:2f684b29d414cd47efe3a3599f390741', 'dropIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES; createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.2-27228', 'keycloak', 'META-INF/jpa-changelog-24.0.2.xml', '2026-04-13 07:43:29.23258', 127, 'EXECUTED', '9:eaee11f6b8aa25d2cc6a84fb86fc6238', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.2-27967-drop-index-if-present', 'keycloak', 'META-INF/jpa-changelog-24.0.2.xml', '2026-04-13 07:43:29.235768', 128, 'MARK_RAN', '9:04baaf56c116ed19951cbc2cca584022', 'dropIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('24.0.2-27967-reindex', 'keycloak', 'META-INF/jpa-changelog-24.0.2.xml', '2026-04-13 07:43:29.239857', 129, 'MARK_RAN', '9:d3d977031d431db16e2c181ce49d73e9', 'createIndex indexName=IDX_CLIENT_ATT_BY_NAME_VALUE, tableName=CLIENT_ATTRIBUTES', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-tables', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.246275', 130, 'EXECUTED', '9:deda2df035df23388af95bbd36c17cef', 'addColumn tableName=OFFLINE_USER_SESSION; addColumn tableName=OFFLINE_CLIENT_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-creation', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.313226', 131, 'EXECUTED', '9:3e96709818458ae49f3c679ae58d263a', 'createIndex indexName=IDX_OFFLINE_USS_BY_LAST_SESSION_REFRESH, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-cleanup-uss-createdon', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.32769', 132, 'EXECUTED', '9:78ab4fc129ed5e8265dbcc3485fba92f', 'dropIndex indexName=IDX_OFFLINE_USS_CREATEDON, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-cleanup-uss-preload', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.33947', 133, 'EXECUTED', '9:de5f7c1f7e10994ed8b62e621d20eaab', 'dropIndex indexName=IDX_OFFLINE_USS_PRELOAD, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-cleanup-uss-by-usersess', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.35375', 134, 'EXECUTED', '9:6eee220d024e38e89c799417ec33667f', 'dropIndex indexName=IDX_OFFLINE_USS_BY_USERSESS, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-cleanup-css-preload', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.36708', 135, 'EXECUTED', '9:5411d2fb2891d3e8d63ddb55dfa3c0c9', 'dropIndex indexName=IDX_OFFLINE_CSS_PRELOAD, tableName=OFFLINE_CLIENT_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-2-mysql', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.369963', 136, 'MARK_RAN', '9:b7ef76036d3126bb83c2423bf4d449d6', 'createIndex indexName=IDX_OFFLINE_USS_BY_BROKER_SESSION_ID, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28265-index-2-not-mysql', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.429798', 137, 'EXECUTED', '9:23396cf51ab8bc1ae6f0cac7f9f6fcf7', 'createIndex indexName=IDX_OFFLINE_USS_BY_BROKER_SESSION_ID, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-org', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.459669', 138, 'EXECUTED', '9:5c859965c2c9b9c72136c360649af157', 'createTable tableName=ORG; addUniqueConstraint constraintName=UK_ORG_NAME, tableName=ORG; addUniqueConstraint constraintName=UK_ORG_GROUP, tableName=ORG; createTable tableName=ORG_DOMAIN', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('unique-consentuser', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.481746', 139, 'EXECUTED', '9:5857626a2ea8767e9a6c66bf3a2cb32f', 'customChange; dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_LOCAL_CONSENT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_EXTERNAL_CONSENT, tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('unique-consentuser-edb-migration', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.498923', 140, 'MARK_RAN', '9:5857626a2ea8767e9a6c66bf3a2cb32f', 'customChange; dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_LOCAL_CONSENT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_EXTERNAL_CONSENT, tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('unique-consentuser-mysql', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.503908', 141, 'MARK_RAN', '9:b79478aad5adaa1bc428e31563f55e8e', 'customChange; dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_LOCAL_CONSENT, tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_EXTERNAL_CONSENT, tableName=...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('25.0.0-28861-index-creation', 'keycloak', 'META-INF/jpa-changelog-25.0.0.xml', '2026-04-13 07:43:29.628455', 142, 'EXECUTED', '9:b9acb58ac958d9ada0fe12a5d4794ab1', 'createIndex indexName=IDX_PERM_TICKET_REQUESTER, tableName=RESOURCE_SERVER_PERM_TICKET; createIndex indexName=IDX_PERM_TICKET_OWNER, tableName=RESOURCE_SERVER_PERM_TICKET', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-org-alias', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.643955', 143, 'EXECUTED', '9:6ef7d63e4412b3c2d66ed179159886a4', 'addColumn tableName=ORG; update tableName=ORG; addNotNullConstraint columnName=ALIAS, tableName=ORG; addUniqueConstraint constraintName=UK_ORG_ALIAS, tableName=ORG', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-org-group', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.664388', 144, 'EXECUTED', '9:da8e8087d80ef2ace4f89d8c5b9ca223', 'addColumn tableName=KEYCLOAK_GROUP; update tableName=KEYCLOAK_GROUP; addNotNullConstraint columnName=TYPE, tableName=KEYCLOAK_GROUP; customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-org-indexes', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.75602', 145, 'EXECUTED', '9:79b05dcd610a8c7f25ec05135eec0857', 'createIndex indexName=IDX_ORG_DOMAIN_ORG_ID, tableName=ORG_DOMAIN', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-org-group-membership', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.774851', 146, 'EXECUTED', '9:a6ace2ce583a421d89b01ba2a28dc2d4', 'addColumn tableName=USER_GROUP_MEMBERSHIP; update tableName=USER_GROUP_MEMBERSHIP; addNotNullConstraint columnName=MEMBERSHIP_TYPE, tableName=USER_GROUP_MEMBERSHIP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('31296-persist-revoked-access-tokens', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.78544', 147, 'EXECUTED', '9:64ef94489d42a358e8304b0e245f0ed4', 'createTable tableName=REVOKED_TOKEN; addPrimaryKey constraintName=CONSTRAINT_RT, tableName=REVOKED_TOKEN', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('31725-index-persist-revoked-access-tokens', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.843695', 148, 'EXECUTED', '9:b994246ec2bf7c94da881e1d28782c7b', 'createIndex indexName=IDX_REV_TOKEN_ON_EXPIRE, tableName=REVOKED_TOKEN', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-idps-for-login', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.931378', 149, 'EXECUTED', '9:51f5fffadf986983d4bd59582c6c1604', 'addColumn tableName=IDENTITY_PROVIDER; createIndex indexName=IDX_IDP_REALM_ORG, tableName=IDENTITY_PROVIDER; createIndex indexName=IDX_IDP_FOR_LOGIN, tableName=IDENTITY_PROVIDER; customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-32583-drop-redundant-index-on-client-session', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.93899', 150, 'EXECUTED', '9:24972d83bf27317a055d234187bb4af9', 'dropIndex indexName=IDX_US_SESS_ID_ON_CL_SESS, tableName=OFFLINE_CLIENT_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0.32582-remove-tables-user-session-user-session-note-and-client-session', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.951555', 151, 'EXECUTED', '9:febdc0f47f2ed241c59e60f58c3ceea5', 'dropTable tableName=CLIENT_SESSION_ROLE; dropTable tableName=CLIENT_SESSION_NOTE; dropTable tableName=CLIENT_SESSION_PROT_MAPPER; dropTable tableName=CLIENT_SESSION_AUTH_STATUS; dropTable tableName=CLIENT_USER_SESSION_NOTE; dropTable tableName=CLI...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.0.0-33201-org-redirect-url', 'keycloak', 'META-INF/jpa-changelog-26.0.0.xml', '2026-04-13 07:43:29.955754', 152, 'EXECUTED', '9:4d0e22b0ac68ebe9794fa9cb752ea660', 'addColumn tableName=ORG', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('29399-jdbc-ping-default', 'keycloak', 'META-INF/jpa-changelog-26.1.0.xml', '2026-04-13 07:43:29.975773', 153, 'EXECUTED', '9:007dbe99d7203fca403b89d4edfdf21e', 'createTable tableName=JGROUPS_PING; addPrimaryKey constraintName=CONSTRAINT_JGROUPS_PING, tableName=JGROUPS_PING', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.1.0-34013', 'keycloak', 'META-INF/jpa-changelog-26.1.0.xml', '2026-04-13 07:43:30.006686', 154, 'EXECUTED', '9:e6b686a15759aef99a6d758a5c4c6a26', 'addColumn tableName=ADMIN_EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.1.0-34380', 'keycloak', 'META-INF/jpa-changelog-26.1.0.xml', '2026-04-13 07:43:30.021394', 155, 'EXECUTED', '9:ac8b9edb7c2b6c17a1c7a11fcf5ccf01', 'dropTable tableName=USERNAME_LOGIN_FAILURE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.0-36750', 'keycloak', 'META-INF/jpa-changelog-26.2.0.xml', '2026-04-13 07:43:30.039789', 156, 'EXECUTED', '9:b49ce951c22f7eb16480ff085640a33a', 'createTable tableName=SERVER_CONFIG', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.0-26106', 'keycloak', 'META-INF/jpa-changelog-26.2.0.xml', '2026-04-13 07:43:30.050266', 157, 'EXECUTED', '9:b5877d5dab7d10ff3a9d209d7beb6680', 'addColumn tableName=CREDENTIAL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.6-39866-duplicate', 'keycloak', 'META-INF/jpa-changelog-26.2.6.xml', '2026-04-13 07:43:30.060016', 158, 'EXECUTED', '9:1dc67ccee24f30331db2cba4f372e40e', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.6-39866-uk', 'keycloak', 'META-INF/jpa-changelog-26.2.6.xml', '2026-04-13 07:43:30.071061', 159, 'EXECUTED', '9:b70b76f47210cf0a5f4ef0e219eac7cd', 'addUniqueConstraint constraintName=UK_MIGRATION_VERSION, tableName=MIGRATION_MODEL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.6-40088-duplicate', 'keycloak', 'META-INF/jpa-changelog-26.2.6.xml', '2026-04-13 07:43:30.079153', 160, 'EXECUTED', '9:cc7e02ed69ab31979afb1982f9670e8f', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.2.6-40088-uk', 'keycloak', 'META-INF/jpa-changelog-26.2.6.xml', '2026-04-13 07:43:30.087357', 161, 'EXECUTED', '9:5bb848128da7bc4595cc507383325241', 'addUniqueConstraint constraintName=UK_MIGRATION_UPDATE_TIME, tableName=MIGRATION_MODEL', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.3.0-groups-description', 'keycloak', 'META-INF/jpa-changelog-26.3.0.xml', '2026-04-13 07:43:30.091436', 162, 'EXECUTED', '9:e1a3c05574326fb5b246b73b9a4c4d49', 'addColumn tableName=KEYCLOAK_GROUP', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.4.0-40933-saml-encryption-attributes', 'keycloak', 'META-INF/jpa-changelog-26.4.0.xml', '2026-04-13 07:43:30.095712', 163, 'EXECUTED', '9:7e9eaba362ca105efdda202303a4fe49', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.4.0-51321', 'keycloak', 'META-INF/jpa-changelog-26.4.0.xml', '2026-04-13 07:43:30.138453', 164, 'EXECUTED', '9:34bab2bc56f75ffd7e347c580874e306', 'createIndex indexName=IDX_EVENT_ENTITY_USER_ID_TYPE, tableName=EVENT_ENTITY', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('40343-workflow-state-table', 'keycloak', 'META-INF/jpa-changelog-26.4.0.xml', '2026-04-13 07:43:30.250911', 165, 'EXECUTED', '9:ed3ab4723ceed210e5b5e60ac4562106', 'createTable tableName=WORKFLOW_STATE; addPrimaryKey constraintName=PK_WORKFLOW_STATE, tableName=WORKFLOW_STATE; addUniqueConstraint constraintName=UQ_WORKFLOW_RESOURCE, tableName=WORKFLOW_STATE; createIndex indexName=IDX_WORKFLOW_STATE_STEP, table...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-index-offline-css-by-client', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.32421', 166, 'EXECUTED', '9:383e981ce95d16e32af757b7998820f7', 'createIndex indexName=IDX_OFFLINE_CSS_BY_CLIENT, tableName=OFFLINE_CLIENT_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-index-offline-css-by-client-storage-provider', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.377833', 167, 'EXECUTED', '9:f5bc200e6fa7d7e483854dee535ca425', 'createIndex indexName=IDX_OFFLINE_CSS_BY_CLIENT_STORAGE_PROVIDER, tableName=OFFLINE_CLIENT_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-idp-config-allow-null-fixed-drop-mssql-index', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.384209', 168, 'MARK_RAN', '9:50c51d2c98cd1d624eb1c485c3cf1f75', 'dropIndex indexName=IDX_IDP_FOR_LOGIN, tableName=IDENTITY_PROVIDER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-idp-config-allow-null', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.393105', 169, 'EXECUTED', '9:b667fb087874303b324c1af7fae4f606', 'dropDefaultValue columnName=TRUST_EMAIL, tableName=IDENTITY_PROVIDER; dropNotNullConstraint columnName=TRUST_EMAIL, tableName=IDENTITY_PROVIDER; dropNotNullConstraint columnName=STORE_TOKEN, tableName=IDENTITY_PROVIDER; dropDefaultValue columnName...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-idp-config-allow-null-fixed-create-mssql-index', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.396369', 170, 'MARK_RAN', '9:dcbbb24c151c3b0b59f12fede23cc94d', 'createIndex indexName=IDX_IDP_FOR_LOGIN, tableName=IDENTITY_PROVIDER', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-remove-workflow-provider-id-column', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.468011', 171, 'EXECUTED', '9:d8eeb324484d45e946d03b953e168b21', 'dropIndex indexName=IDX_WORKFLOW_STATE_PROVIDER, tableName=WORKFLOW_STATE; createIndex indexName=IDX_WORKFLOW_STATE_PROVIDER, tableName=WORKFLOW_STATE; dropColumn columnName=WORKFLOW_PROVIDER_ID, tableName=WORKFLOW_STATE', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-add-remember-me', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.476576', 172, 'EXECUTED', '9:a7273ea8b21bd2f674c9c49141999f05', 'addColumn tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-add-sess-refresh-idx', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.54954', 173, 'EXECUTED', '9:ce49383d317ccbcd3434d1f21172b0b7', 'createIndex indexName=IDX_USER_SESSION_EXPIRATION_CREATED, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-add-sess-create-idx', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.591817', 174, 'EXECUTED', '9:aaee09e23a4d8468fbc5c51b7b314c58', 'createIndex indexName=IDX_USER_SESSION_EXPIRATION_LAST_REFRESH, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-drop-sess-refresh-idx', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.607455', 175, 'EXECUTED', '9:f0082210b6ccbbaf81287c27aa23753c', 'dropIndex indexName=IDX_OFFLINE_USS_BY_LAST_SESSION_REFRESH, tableName=OFFLINE_USER_SESSION', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-mysql-mariadb-default-charset-collation', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.610302', 176, 'MARK_RAN', '9:1b383fa60d2db0a8952b365e725f9d16', 'customChange', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.5.0-invitations-table-fixed2', 'keycloak', 'META-INF/jpa-changelog-26.5.0.xml', '2026-04-13 07:43:30.738537', 177, 'EXECUTED', '9:322cb11fc03181903dcd67a54f8b3cf0', 'createTable tableName=ORG_INVITATION; addForeignKeyConstraint baseTableName=ORG_INVITATION, constraintName=FK_ORG_INVITATION_ORG, referencedTableName=ORG; createIndex indexName=IDX_ORG_INVITATION_ORG_ID, tableName=ORG_INVITATION; createIndex index...', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.6.0-45009-broker-link-user-id', 'keycloak', 'META-INF/jpa-changelog-26.6.0.xml', '2026-04-13 07:43:30.811972', 178, 'EXECUTED', '9:05026bbbc8d2ead5afcbda2f5fdf3a2b', 'createIndex indexName=IDX_BROKER_LINK_USER_ID, tableName=BROKER_LINK', '', NULL, '4.33.0', NULL, NULL, '6066184922');
INSERT INTO keycloak.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) VALUES ('26.6.0-45009-broker-link-identity-provider', 'keycloak', 'META-INF/jpa-changelog-26.6.0.xml', '2026-04-13 07:43:30.881878', 179, 'EXECUTED', '9:7d9a0253c9de7be754efef8bba4265bd', 'createIndex indexName=IDX_BROKER_LINK_IDENTITY_PROVIDER, tableName=BROKER_LINK', '', NULL, '4.33.0', NULL, NULL, '6066184922');


--
-- Data for Name: databasechangeloglock; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.databasechangeloglock (id, locked, lockgranted, lockedby) VALUES (1, false, NULL, NULL);
INSERT INTO keycloak.databasechangeloglock (id, locked, lockgranted, lockedby) VALUES (1000, false, NULL, NULL);


--
-- Data for Name: default_client_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'edd03863-01ef-4156-8b0b-0cbd87959c4d', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '68017d7b-7c27-4bc6-8346-348fc25f92d2', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '620a3cd4-2f16-43f8-8c86-8123af3f410d', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '07effd1e-fb39-4217-8cd0-bd8744c37376', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'da0c0f2d-cf22-4514-ad78-1e3864a5d873', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '87094c14-6111-47ee-8bea-6f77339383cf', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '404593df-a9d2-47e7-a7b4-b5549cfdf9f5', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '9014bdd1-1091-452c-9c01-58d05f8002af', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'a9740ed8-189f-4138-82df-5f4b05994d5e', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', '7b79221b-2aef-4b37-bb4b-d0b93032facf', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '09b540d4-e59e-42bb-a28d-ef6381c94dac', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '1db071da-7320-4393-b435-ac8d8041e7b0', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '688eff0e-5e56-492a-9503-8644d6e8c4c2', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '05f865b2-1093-4731-b3d0-c07daa54ca11', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '158e3a24-8cb8-49f5-8631-0fbb4e8daf82', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '50a80748-2a11-4841-9e9e-5ec88b78aaad', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '54bab3f8-b662-4249-b82c-7f01f7237124', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '75cbc876-53fd-422e-b104-b5d420e71dd6', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'ceb5a1ef-c8f8-4461-9c45-4062ac058424', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '6fd65251-100b-4201-951c-037b8e658177', false);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'c1da6476-297c-4a19-b6ae-9c3889533aa9', true);
INSERT INTO keycloak.default_client_scope (realm_id, scope_id, default_scope) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '43494a79-3bc5-4c7b-b7e5-8c67caf31365', false);


--
-- Data for Name: event_entity; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_consent; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_consent_cl_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_credential; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_group_membership; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_required_action; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: fed_user_role_mapping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: federated_identity; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: federated_user; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: keycloak_group; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: group_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: group_role_mapping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: identity_provider; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: identity_provider_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: identity_provider_mapper; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: idp_mapper_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: jgroups_ping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: migration_model; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.migration_model (id, version, update_time) VALUES ('d79tx', '26.5.7', 1776066215);


--
-- Data for Name: offline_client_session; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.offline_client_session (user_session_id, client_id, offline_flag, "timestamp", data, client_storage_provider, external_client_id, version) VALUES ('G_d2_vW92SE2b1biYJVGk2hP', 'aa678413-b137-42ed-9dde-703b126d7d5f', '0', 1778475357, '{"authMethod":"openid-connect","notes":{"clientId":"aa678413-b137-42ed-9dde-703b126d7d5f","userSessionStartedAt":"1778475357","iss":"https://app.acom-offer-desk.ru/iam/realms/master","startedAt":"1778475357","level-of-authentication":"-1"}}', 'local', 'local', 0);
INSERT INTO keycloak.offline_client_session (user_session_id, client_id, offline_flag, "timestamp", data, client_storage_provider, external_client_id, version) VALUES ('oJnXZTxk6cE4Rld3FDod-ETD', 'aa678413-b137-42ed-9dde-703b126d7d5f', '0', 1778475381, '{"authMethod":"openid-connect","notes":{"clientId":"aa678413-b137-42ed-9dde-703b126d7d5f","userSessionStartedAt":"1778475381","iss":"https://app.acom-offer-desk.ru/iam/realms/master","startedAt":"1778475381","level-of-authentication":"-1"}}', 'local', 'local', 0);


--
-- Data for Name: offline_user_session; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.offline_user_session (user_session_id, user_id, realm_id, created_on, offline_flag, data, last_session_refresh, broker_session_id, version, remember_me) VALUES ('G_d2_vW92SE2b1biYJVGk2hP', '95dcda34-2f55-4380-ac6d-f93310f1b321', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 1778475357, '0', '{"ipAddress":"127.0.0.1","authMethod":"openid-connect","rememberMe":false,"started":0,"notes":{"KC_DEVICE_NOTE":"eyJpcEFkZHJlc3MiOiIxMjcuMC4wLjEiLCJvcyI6Ik90aGVyIiwib3NWZXJzaW9uIjoiVW5rbm93biIsImJyb3dzZXIiOiJBcGFjaGUtSHR0cENsaWVudC80LjUuMTQiLCJkZXZpY2UiOiJPdGhlciIsImxhc3RBY2Nlc3MiOjAsIm1vYmlsZSI6ZmFsc2V9","authenticators-completed":"{\"fe456a1c-605b-4f45-954b-b1e7393335cf\":1778475357,\"010d6006-ccaa-4017-954a-9beac22fb7cb\":1778475357}"},"state":"LOGGED_IN"}', 1778475357, NULL, 0, false);
INSERT INTO keycloak.offline_user_session (user_session_id, user_id, realm_id, created_on, offline_flag, data, last_session_refresh, broker_session_id, version, remember_me) VALUES ('oJnXZTxk6cE4Rld3FDod-ETD', '95dcda34-2f55-4380-ac6d-f93310f1b321', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 1778475381, '0', '{"ipAddress":"127.0.0.1","authMethod":"openid-connect","rememberMe":false,"started":0,"notes":{"KC_DEVICE_NOTE":"eyJpcEFkZHJlc3MiOiIxMjcuMC4wLjEiLCJvcyI6Ik90aGVyIiwib3NWZXJzaW9uIjoiVW5rbm93biIsImJyb3dzZXIiOiJBcGFjaGUtSHR0cENsaWVudC80LjUuMTQiLCJkZXZpY2UiOiJPdGhlciIsImxhc3RBY2Nlc3MiOjAsIm1vYmlsZSI6ZmFsc2V9","authenticators-completed":"{\"fe456a1c-605b-4f45-954b-b1e7393335cf\":1778475381,\"010d6006-ccaa-4017-954a-9beac22fb7cb\":1778475381}"},"state":"LOGGED_IN"}', 1778475381, NULL, 0, false);


--
-- Data for Name: org; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: org_domain; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: org_invitation; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: policy_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: protocol_mapper; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('ab768ab0-620c-44ff-bf18-e4f4c8d17e54', 'audience resolve', 'openid-connect', 'oidc-audience-resolve-mapper', 'd8f91de3-502b-4561-89b7-ee7dc8ac8b64', NULL);
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'locale', 'openid-connect', 'oidc-usermodel-attribute-mapper', '6126224e-eca8-41cf-bebe-da15f56c0111', NULL);
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('6d51b335-4bde-46d2-896a-baece29fae2d', 'role list', 'saml', 'saml-role-list-mapper', NULL, '68017d7b-7c27-4bc6-8346-348fc25f92d2');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('69402f97-d4c5-4076-b5be-7da2c445838c', 'organization', 'saml', 'saml-organization-membership-mapper', NULL, '620a3cd4-2f16-43f8-8c86-8123af3f410d');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('eedac44e-d92d-4b47-9439-2c2ded15de07', 'full name', 'openid-connect', 'oidc-full-name-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'family name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'given name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'middle name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'nickname', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'username', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'profile', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'picture', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'website', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'gender', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'birthdate', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'zoneinfo', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'locale', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'updated at', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '07effd1e-fb39-4217-8cd0-bd8744c37376');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'email', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, 'da0c0f2d-cf22-4514-ad78-1e3864a5d873');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'email verified', 'openid-connect', 'oidc-usermodel-property-mapper', NULL, 'da0c0f2d-cf22-4514-ad78-1e3864a5d873');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'address', 'openid-connect', 'oidc-address-mapper', NULL, '87094c14-6111-47ee-8bea-6f77339383cf');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'phone number', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '404593df-a9d2-47e7-a7b4-b5549cfdf9f5');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'phone number verified', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '404593df-a9d2-47e7-a7b4-b5549cfdf9f5');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'realm roles', 'openid-connect', 'oidc-usermodel-realm-role-mapper', NULL, '9014bdd1-1091-452c-9c01-58d05f8002af');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'client roles', 'openid-connect', 'oidc-usermodel-client-role-mapper', NULL, '9014bdd1-1091-452c-9c01-58d05f8002af');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e41f5c1e-5168-4ed2-8fc7-c5725599cb6b', 'audience resolve', 'openid-connect', 'oidc-audience-resolve-mapper', NULL, '9014bdd1-1091-452c-9c01-58d05f8002af');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('d822af08-9a50-4ab6-9db2-b5995a4ff942', 'allowed web origins', 'openid-connect', 'oidc-allowed-origins-mapper', NULL, '72f83650-ebf5-49a3-8c0c-5063b8d1ddf0');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'upn', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'groups', 'openid-connect', 'oidc-usermodel-realm-role-mapper', NULL, 'a0f3f80a-eab4-4ad6-9d2a-fc0fd2035494');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('094217ef-d81a-4b6d-bed3-b977d38cee78', 'acr loa level', 'openid-connect', 'oidc-acr-mapper', NULL, 'a9740ed8-189f-4138-82df-5f4b05994d5e');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'auth_time', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '7b79221b-2aef-4b37-bb4b-d0b93032facf');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('437c0780-fdd5-4800-a294-bca9abc593fc', 'sub', 'openid-connect', 'oidc-sub-mapper', NULL, '7b79221b-2aef-4b37-bb4b-d0b93032facf');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'Client ID', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '8abf3b84-3370-4855-a511-3c3c32d2743f');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'Client Host', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '8abf3b84-3370-4855-a511-3c3c32d2743f');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'Client IP Address', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '8abf3b84-3370-4855-a511-3c3c32d2743f');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'organization', 'openid-connect', 'oidc-organization-membership-mapper', NULL, 'b6f4182b-c66d-4f4b-9a1d-c715b4ba8b2a');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('7915def2-1d90-4a55-aad0-4dc66c12c279', 'audience resolve', 'openid-connect', 'oidc-audience-resolve-mapper', 'b95dd4dd-8d21-4040-873f-7788a96780ce', NULL);
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('a193547a-ae26-4853-85c2-955a8018362a', 'role list', 'saml', 'saml-role-list-mapper', NULL, '1db071da-7320-4393-b435-ac8d8041e7b0');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('34756305-3aae-4de0-a27d-2213076ada72', 'organization', 'saml', 'saml-organization-membership-mapper', NULL, '688eff0e-5e56-492a-9503-8644d6e8c4c2');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('0781a1f0-45ee-417b-b978-ec137cd5e2e3', 'full name', 'openid-connect', 'oidc-full-name-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'family name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'given name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'middle name', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'nickname', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'username', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'profile', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'picture', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'website', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'gender', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'birthdate', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'zoneinfo', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'locale', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'updated at', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '05f865b2-1093-4731-b3d0-c07daa54ca11');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'email', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '158e3a24-8cb8-49f5-8631-0fbb4e8daf82');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'email verified', 'openid-connect', 'oidc-usermodel-property-mapper', NULL, '158e3a24-8cb8-49f5-8631-0fbb4e8daf82');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'address', 'openid-connect', 'oidc-address-mapper', NULL, '50a80748-2a11-4841-9e9e-5ec88b78aaad');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'phone number', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '54bab3f8-b662-4249-b82c-7f01f7237124');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'phone number verified', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '54bab3f8-b662-4249-b82c-7f01f7237124');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'realm roles', 'openid-connect', 'oidc-usermodel-realm-role-mapper', NULL, '75cbc876-53fd-422e-b104-b5d420e71dd6');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'client roles', 'openid-connect', 'oidc-usermodel-client-role-mapper', NULL, '75cbc876-53fd-422e-b104-b5d420e71dd6');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('f93e0448-7614-463f-b512-dc3b7b38b981', 'audience resolve', 'openid-connect', 'oidc-audience-resolve-mapper', NULL, '75cbc876-53fd-422e-b104-b5d420e71dd6');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('c2753168-c1cc-4099-946b-d5e4edd317c9', 'allowed web origins', 'openid-connect', 'oidc-allowed-origins-mapper', NULL, 'ceb5a1ef-c8f8-4461-9c45-4062ac058424');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'upn', 'openid-connect', 'oidc-usermodel-attribute-mapper', NULL, '6fd65251-100b-4201-951c-037b8e658177');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'groups', 'openid-connect', 'oidc-usermodel-realm-role-mapper', NULL, '6fd65251-100b-4201-951c-037b8e658177');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('4bd28d4d-28d0-4f79-b253-c8c806003774', 'acr loa level', 'openid-connect', 'oidc-acr-mapper', NULL, '7fef3fdd-f347-4ba1-9588-51ebc0f5fe66');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'auth_time', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, 'c1da6476-297c-4a19-b6ae-9c3889533aa9');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('6cd0bb43-a6a4-4cd8-bd10-09cb1ba063bf', 'sub', 'openid-connect', 'oidc-sub-mapper', NULL, 'c1da6476-297c-4a19-b6ae-9c3889533aa9');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'Client ID', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '632ace5c-68c7-49dc-9833-f81bd49649b9');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'Client Host', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '632ace5c-68c7-49dc-9833-f81bd49649b9');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'Client IP Address', 'openid-connect', 'oidc-usersessionmodel-note-mapper', NULL, '632ace5c-68c7-49dc-9833-f81bd49649b9');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'organization', 'openid-connect', 'oidc-organization-membership-mapper', NULL, '43494a79-3bc5-4c7b-b7e5-8c67caf31365');
INSERT INTO keycloak.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'locale', 'openid-connect', 'oidc-usermodel-attribute-mapper', '775ebc9e-a65c-4635-8bfe-01b7c02a581b', NULL);


--
-- Data for Name: protocol_mapper_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'locale', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'locale', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2ad0d10e-40cf-4a08-a525-b64419f808db', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6d51b335-4bde-46d2-896a-baece29fae2d', 'false', 'single');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6d51b335-4bde-46d2-896a-baece29fae2d', 'Basic', 'attribute.nameformat');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6d51b335-4bde-46d2-896a-baece29fae2d', 'Role', 'attribute.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'lastName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'family_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('019f17de-467e-4ed6-ad34-85a926d4bf7f', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'profile', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'profile', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('157fb389-15bf-47cb-b1e1-697b9004057a', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'zoneinfo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'zoneinfo', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('264e0a2e-92e7-4ae2-ae9b-3a45a2eb8be2', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'middleName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'middle_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2b085456-85ad-4998-9a8e-7fdf276a7df5', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'username', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'preferred_username', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('461e96e7-886b-4f31-9db0-7f1ebfe9a3e2', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'picture', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'picture', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4a5cfc6c-57ab-47c5-a85b-d6186ec94482', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'firstName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'given_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('5a48f918-64c1-4c93-979e-b147f2323ed2', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'birthdate', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'birthdate', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('7bf76d2f-a93f-4b47-b311-fc7b6a32994d', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'website', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'website', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('9630a1f1-1693-4d76-9020-256a674b3c54', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'nickname', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'nickname', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a5f774fa-21f2-4742-be27-ef55780b3c6e', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'updatedAt', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'updated_at', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ae706a91-5657-4357-bd9f-5d23a23f5d68', 'long', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'gender', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'gender', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e396bbd0-0540-48ff-a49c-15924b505720', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'locale', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'locale', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ed609257-d9a5-4ff8-ab11-703d196cf322', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('eedac44e-d92d-4b47-9439-2c2ded15de07', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('eedac44e-d92d-4b47-9439-2c2ded15de07', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('eedac44e-d92d-4b47-9439-2c2ded15de07', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('eedac44e-d92d-4b47-9439-2c2ded15de07', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'emailVerified', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'email_verified', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('716cf67a-3b4c-4813-900d-d591cde4b34b', 'boolean', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'email', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'email', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ff159975-9b33-43e6-bdea-ccc2b61d9b06', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'formatted', 'user.attribute.formatted');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'country', 'user.attribute.country');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'postal_code', 'user.attribute.postal_code');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'street', 'user.attribute.street');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'region', 'user.attribute.region');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('463a0785-2909-46af-a3bc-11678ea780e2', 'locality', 'user.attribute.locality');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'phoneNumberVerified', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'phone_number_verified', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('04855b0d-abdc-4717-8202-e4e1d8d985cc', 'boolean', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'phoneNumber', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'phone_number', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('758c4786-f5d3-4ba4-889f-028a19a7c8a2', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'resource_access.${client_id}.roles', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('34f83bcc-e98b-4228-85f3-2a63c08dc1b0', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'realm_access.roles', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('58405276-b1f3-438c-98aa-168768c0116f', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e41f5c1e-5168-4ed2-8fc7-c5725599cb6b', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e41f5c1e-5168-4ed2-8fc7-c5725599cb6b', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('d822af08-9a50-4ab6-9db2-b5995a4ff942', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('d822af08-9a50-4ab6-9db2-b5995a4ff942', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'groups', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('090d6100-f908-4a5c-9384-4b22acd9061c', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'username', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'upn', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e032026c-240f-45c0-b6fb-5f524e46b68d', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('094217ef-d81a-4b6d-bed3-b977d38cee78', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('094217ef-d81a-4b6d-bed3-b977d38cee78', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('094217ef-d81a-4b6d-bed3-b977d38cee78', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('437c0780-fdd5-4800-a294-bca9abc593fc', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('437c0780-fdd5-4800-a294-bca9abc593fc', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'AUTH_TIME', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'auth_time', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c4ecdec7-2742-4d81-904d-28168760eeee', 'long', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'clientHost', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'clientHost', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3cf3c761-dfc2-47d4-9ccd-123e14e0c41a', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'client_id', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'client_id', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cc288810-6c63-45a7-877d-3c7e5d008385', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'clientAddress', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'clientAddress', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e1270727-55c6-4e05-befb-2e33b42c13bc', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'organization', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b2ac03a4-82b3-45c8-8819-2348c142b1ec', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a193547a-ae26-4853-85c2-955a8018362a', 'false', 'single');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a193547a-ae26-4853-85c2-955a8018362a', 'Basic', 'attribute.nameformat');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('a193547a-ae26-4853-85c2-955a8018362a', 'Role', 'attribute.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0781a1f0-45ee-417b-b978-ec137cd5e2e3', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0781a1f0-45ee-417b-b978-ec137cd5e2e3', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0781a1f0-45ee-417b-b978-ec137cd5e2e3', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0781a1f0-45ee-417b-b978-ec137cd5e2e3', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'username', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'preferred_username', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('12b8557f-3469-48d0-aa3a-000c3d9516a0', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'firstName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'given_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('13b55ef3-09d3-4c35-86f7-91fc97587033', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'nickname', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'nickname', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('1b935651-9767-4ec8-b937-e9dff6db00f2', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'locale', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'locale', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2cbbac55-973a-432c-8142-409c205f9b9b', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'gender', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'gender', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('488b90e4-bc4f-4b79-a075-d88dff8b543b', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'zoneinfo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'zoneinfo', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8147b593-7733-4645-9cc1-340135a712b1', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'website', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'website', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8a3b27a9-f3c1-4ff6-899b-fbe032f67ad4', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'birthdate', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'birthdate', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8d74cd3e-3522-4fde-be94-64e9a3fd3827', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'profile', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'profile', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('8ef48d1a-d510-47cf-81ab-c56da53713b0', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'updatedAt', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'updated_at', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('961618c5-e309-44e5-997e-5c4f272a719a', 'long', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'picture', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'picture', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c0b5d303-d1b5-469c-b303-d8ed98c3f735', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'lastName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'family_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e0b553ca-8c11-4b67-9df7-e096a6334e2d', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'middleName', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'middle_name', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f08e76c2-18ca-488f-96a9-3f1f8c7f11e6', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'email', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'email', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2f35ba93-f5bf-42af-a1e2-2d600e4ecf32', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'emailVerified', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'email_verified', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3e8cbb8a-a12e-4f95-94c1-b077cbd1fe1c', 'boolean', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'formatted', 'user.attribute.formatted');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'country', 'user.attribute.country');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'postal_code', 'user.attribute.postal_code');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'street', 'user.attribute.street');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'region', 'user.attribute.region');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('ce405961-f431-454f-b14e-b12f8889528f', 'locality', 'user.attribute.locality');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'phoneNumberVerified', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'phone_number_verified', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('2590f2a4-d5aa-47dd-b7b3-31fbc3e5087d', 'boolean', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'phoneNumber', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'phone_number', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('3ed40259-c96b-4ccc-a41c-e6560d27ec94', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'realm_access.roles', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('459f4da1-0ad1-4d34-a304-e2bfa47ba870', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'resource_access.${client_id}.roles', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('abd4d3fe-583c-4703-8780-779a75df752c', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f93e0448-7614-463f-b512-dc3b7b38b981', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('f93e0448-7614-463f-b512-dc3b7b38b981', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c2753168-c1cc-4099-946b-d5e4edd317c9', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('c2753168-c1cc-4099-946b-d5e4edd317c9', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'username', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'upn', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('0f2a03fe-813d-46ec-9db4-0c25a1eebf37', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'foo', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'groups', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b0bc4487-bdf9-4cb9-8aed-5d2af26be66d', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4bd28d4d-28d0-4f79-b253-c8c806003774', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4bd28d4d-28d0-4f79-b253-c8c806003774', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('4bd28d4d-28d0-4f79-b253-c8c806003774', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6cd0bb43-a6a4-4cd8-bd10-09cb1ba063bf', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6cd0bb43-a6a4-4cd8-bd10-09cb1ba063bf', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'AUTH_TIME', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'auth_time', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('b6bbeeff-0198-4dab-9cfd-42018928906c', 'long', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'clientAddress', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'clientAddress', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('51db41e6-4e73-47a8-a3c1-a2a55a57dad6', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'clientHost', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'clientHost', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('cb5f035a-4a40-40ed-84da-58fdc8ab6d72', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'client_id', 'user.session.note');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'client_id', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('faccf451-c4cf-4914-b2cb-c149381b8b94', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'true', 'multivalued');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'organization', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('e6de04db-1248-4d6f-a68a-0b0081646c8c', 'String', 'jsonType.label');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'true', 'introspection.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'true', 'userinfo.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'locale', 'user.attribute');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'true', 'id.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'true', 'access.token.claim');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'locale', 'claim.name');
INSERT INTO keycloak.protocol_mapper_config (protocol_mapper_id, value, name) VALUES ('6c77d79a-7b9b-4334-b051-9726f9d8ae5d', 'String', 'jsonType.label');


--
-- Data for Name: realm_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.contentSecurityPolicyReportOnly', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xContentTypeOptions', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'nosniff');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.referrerPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'no-referrer');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xRobotsTag', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'none');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xFrameOptions', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'SAMEORIGIN');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.contentSecurityPolicy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'frame-src ''self''; frame-ancestors ''self''; object-src ''none'';');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.strictTransportSecurity', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'max-age=31536000; includeSubDomains');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('bruteForceProtected', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('permanentLockout', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxTemporaryLockouts', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '0');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('bruteForceStrategy', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'MULTIPLE');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxFailureWaitSeconds', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '900');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('minimumQuickLoginWaitSeconds', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '60');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('waitIncrementSeconds', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '60');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('quickLoginCheckMilliSeconds', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '1000');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxDeltaTimeSeconds', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '43200');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('failureFactor', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '30');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('realmReusableOtpCode', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('firstBrokerLoginFlowId', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'ec0d9a43-9b62-48cc-800d-0ddc8eed35d7');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('displayName', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'Keycloak');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('displayNameHtml', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '<div class="kc-logo-text"><span>Keycloak</span></div>');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('defaultSignatureAlgorithm', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'RS256');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('offlineSessionMaxLifespanEnabled', '273f6fe8-dc27-45b7-815b-a759a2722e8f', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('offlineSessionMaxLifespan', '273f6fe8-dc27-45b7-815b-a759a2722e8f', '5184000');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.contentSecurityPolicyReportOnly', '6b03f9aa-9012-46b3-a691-480d464101db', '');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xContentTypeOptions', '6b03f9aa-9012-46b3-a691-480d464101db', 'nosniff');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.referrerPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'no-referrer');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xRobotsTag', '6b03f9aa-9012-46b3-a691-480d464101db', 'none');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.xFrameOptions', '6b03f9aa-9012-46b3-a691-480d464101db', 'SAMEORIGIN');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.contentSecurityPolicy', '6b03f9aa-9012-46b3-a691-480d464101db', 'frame-src ''self''; frame-ancestors ''self''; object-src ''none'';');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('_browser_header.strictTransportSecurity', '6b03f9aa-9012-46b3-a691-480d464101db', 'max-age=31536000; includeSubDomains');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('permanentLockout', '6b03f9aa-9012-46b3-a691-480d464101db', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxTemporaryLockouts', '6b03f9aa-9012-46b3-a691-480d464101db', '0');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('bruteForceStrategy', '6b03f9aa-9012-46b3-a691-480d464101db', 'MULTIPLE');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxFailureWaitSeconds', '6b03f9aa-9012-46b3-a691-480d464101db', '900');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('minimumQuickLoginWaitSeconds', '6b03f9aa-9012-46b3-a691-480d464101db', '60');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('waitIncrementSeconds', '6b03f9aa-9012-46b3-a691-480d464101db', '60');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('quickLoginCheckMilliSeconds', '6b03f9aa-9012-46b3-a691-480d464101db', '1000');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('maxDeltaTimeSeconds', '6b03f9aa-9012-46b3-a691-480d464101db', '43200');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('failureFactor', '6b03f9aa-9012-46b3-a691-480d464101db', '30');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('realmReusableOtpCode', '6b03f9aa-9012-46b3-a691-480d464101db', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('displayName', '6b03f9aa-9012-46b3-a691-480d464101db', 'AcomOfferDesk');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('defaultSignatureAlgorithm', '6b03f9aa-9012-46b3-a691-480d464101db', 'RS256');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('bruteForceProtected', '6b03f9aa-9012-46b3-a691-480d464101db', 'true');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('offlineSessionMaxLifespanEnabled', '6b03f9aa-9012-46b3-a691-480d464101db', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('offlineSessionMaxLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '5184000');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('actionTokenGeneratedByAdminLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '43200');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('oauth2DeviceCodeLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '600');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('oauth2DevicePollingInterval', '6b03f9aa-9012-46b3-a691-480d464101db', '5');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRpEntityName', '6b03f9aa-9012-46b3-a691-480d464101db', 'keycloak');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicySignatureAlgorithms', '6b03f9aa-9012-46b3-a691-480d464101db', 'ES256,RS256');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRpId', '6b03f9aa-9012-46b3-a691-480d464101db', '');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAttestationConveyancePreference', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAuthenticatorAttachment', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRequireResidentKey', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyUserVerificationRequirement', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyCreateTimeout', '6b03f9aa-9012-46b3-a691-480d464101db', '0');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAvoidSameAuthenticatorRegister', '6b03f9aa-9012-46b3-a691-480d464101db', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRpEntityNamePasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'keycloak');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicySignatureAlgorithmsPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'ES256,RS256');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRpIdPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', '');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAttestationConveyancePreferencePasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAuthenticatorAttachmentPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'not specified');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyRequireResidentKeyPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'Yes');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyUserVerificationRequirementPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'required');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyCreateTimeoutPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', '0');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('webAuthnPolicyAvoidSameAuthenticatorRegisterPasswordless', '6b03f9aa-9012-46b3-a691-480d464101db', 'false');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('cibaBackchannelTokenDeliveryMode', '6b03f9aa-9012-46b3-a691-480d464101db', 'poll');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('cibaExpiresIn', '6b03f9aa-9012-46b3-a691-480d464101db', '120');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('cibaInterval', '6b03f9aa-9012-46b3-a691-480d464101db', '5');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('cibaAuthRequestedUserHint', '6b03f9aa-9012-46b3-a691-480d464101db', 'login_hint');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('parRequestUriLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '60');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('firstBrokerLoginFlowId', '6b03f9aa-9012-46b3-a691-480d464101db', '8d8742ad-d3ce-43ae-a921-2538f1ca162f');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('clientSessionIdleTimeout', '6b03f9aa-9012-46b3-a691-480d464101db', '1800');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('clientSessionMaxLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '86400');
INSERT INTO keycloak.realm_attribute (name, realm_id, value) VALUES ('actionTokenGeneratedByUserLifespan', '6b03f9aa-9012-46b3-a691-480d464101db', '1800');


--
-- Data for Name: realm_default_groups; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: realm_enabled_event_types; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: realm_events_listeners; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm_events_listeners (realm_id, value) VALUES ('273f6fe8-dc27-45b7-815b-a759a2722e8f', 'jboss-logging');
INSERT INTO keycloak.realm_events_listeners (realm_id, value) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'jboss-logging');


--
-- Data for Name: realm_localizations; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: realm_required_credential; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm_required_credential (type, form_label, input, secret, realm_id) VALUES ('password', 'password', true, true, '273f6fe8-dc27-45b7-815b-a759a2722e8f');
INSERT INTO keycloak.realm_required_credential (type, form_label, input, secret, realm_id) VALUES ('password', 'password', true, true, '6b03f9aa-9012-46b3-a691-480d464101db');


--
-- Data for Name: realm_smtp_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'bykgytqzenzlyjdw', 'password');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'false', 'starttls');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'true', 'auth');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', '465', 'port');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'smtp.yandex.com', 'host');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'smirnovaalex.s.s@yandex.ru', 'replyTo');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'smirnovaalex.s.s@yandex.ru', 'from');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'AcomOfferDesk', 'fromDisplayName');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'smirnovaalex.s.s@yandex.ru', 'user');
INSERT INTO keycloak.realm_smtp_config (realm_id, value, name) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'true', 'ssl');


--
-- Data for Name: realm_supported_locales; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.realm_supported_locales (realm_id, value) VALUES ('6b03f9aa-9012-46b3-a691-480d464101db', 'ru');


--
-- Data for Name: redirect_uris; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('2e3b661d-6818-4c49-8d14-202bae329f7f', '/realms/master/account/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', '/realms/master/account/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '/admin/master/console/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('5741792b-35db-4f5f-9aba-26f2c5b81be5', '/realms/acom-offerdesk/account/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '/realms/acom-offerdesk/account/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '/admin/acom-offerdesk/console/*');
INSERT INTO keycloak.redirect_uris (client_id, value) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', 'https://app.acom-offer-desk.ru/api/v1/auth/callback');


--
-- Data for Name: required_action_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: required_action_provider; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('2fdd20b4-c877-4249-928e-209723410132', 'VERIFY_EMAIL', 'Verify Email', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'VERIFY_EMAIL', 50);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('04ebad1c-23d0-4757-af37-047f1f01ec58', 'UPDATE_PROFILE', 'Update Profile', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'UPDATE_PROFILE', 40);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('31aa756b-46df-4c7f-9750-1f635e1f2938', 'CONFIGURE_TOTP', 'Configure OTP', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'CONFIGURE_TOTP', 10);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('4bd28cf0-58ee-4ded-a808-91bc8826ba10', 'UPDATE_PASSWORD', 'Update Password', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'UPDATE_PASSWORD', 30);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('76ca21ca-05ad-415a-8fa8-d1de374fcc01', 'TERMS_AND_CONDITIONS', 'Terms and Conditions', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, false, 'TERMS_AND_CONDITIONS', 20);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('aced4f0d-850b-4899-b30c-c767a28cbde1', 'delete_account', 'Delete Account', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, false, 'delete_account', 60);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('96ef75b2-d011-46aa-81bd-b579487cfee1', 'delete_credential', 'Delete Credential', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'delete_credential', 110);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('eb047879-a5d7-4d12-a71f-caf69e7d28f8', 'update_user_locale', 'Update User Locale', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'update_user_locale', 1000);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('083564f9-468d-42f8-80c6-dc3f97e1b182', 'UPDATE_EMAIL', 'Update Email', '273f6fe8-dc27-45b7-815b-a759a2722e8f', false, false, 'UPDATE_EMAIL', 70);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('ab7a4bf1-e5af-4e24-bdc0-3fb926eecc07', 'CONFIGURE_RECOVERY_AUTHN_CODES', 'Recovery Authentication Codes', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'CONFIGURE_RECOVERY_AUTHN_CODES', 130);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('803500a4-7707-48eb-a073-0fd46a07bf80', 'webauthn-register', 'Webauthn Register', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'webauthn-register', 80);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('322141af-65bb-4eef-9aa7-2ab1025556dd', 'webauthn-register-passwordless', 'Webauthn Register Passwordless', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'webauthn-register-passwordless', 90);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('68e1cd31-521e-4c2f-a6a6-0cb9e1c11b67', 'VERIFY_PROFILE', 'Verify Profile', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'VERIFY_PROFILE', 100);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('e0dfdb22-b5bb-40e7-9582-575eba234c0c', 'idp_link', 'Linking Identity Provider', '273f6fe8-dc27-45b7-815b-a759a2722e8f', true, false, 'idp_link', 120);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('9c813fc4-539b-4bf1-a6a1-72cd3f61ec54', 'VERIFY_EMAIL', 'Verify Email', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'VERIFY_EMAIL', 50);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('7222a725-2b30-465a-a67b-047e45608f66', 'UPDATE_PROFILE', 'Update Profile', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'UPDATE_PROFILE', 40);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('69ff119f-88df-44d4-a010-259d18a8a056', 'CONFIGURE_TOTP', 'Configure OTP', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'CONFIGURE_TOTP', 10);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('4e85f0bf-26a5-4d4c-a1a1-c83f005e3a5c', 'UPDATE_PASSWORD', 'Update Password', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'UPDATE_PASSWORD', 30);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('a77688b7-32dd-4d4f-af7a-c13f868c932f', 'TERMS_AND_CONDITIONS', 'Terms and Conditions', '6b03f9aa-9012-46b3-a691-480d464101db', false, false, 'TERMS_AND_CONDITIONS', 20);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('475fc5f9-225c-4304-a6c0-1d0361ac5612', 'delete_account', 'Delete Account', '6b03f9aa-9012-46b3-a691-480d464101db', false, false, 'delete_account', 60);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('c57ee28d-9a81-4cf8-991c-0f003deed2a8', 'delete_credential', 'Delete Credential', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'delete_credential', 110);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('5d9c9e56-a0a6-4fd0-939e-fe3abe1933bc', 'update_user_locale', 'Update User Locale', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'update_user_locale', 1000);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('afe3522b-22ce-4384-a5e5-245f56796a22', 'UPDATE_EMAIL', 'Update Email', '6b03f9aa-9012-46b3-a691-480d464101db', false, false, 'UPDATE_EMAIL', 70);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('33ae6aac-c345-4483-8864-a6025a365bd5', 'CONFIGURE_RECOVERY_AUTHN_CODES', 'Recovery Authentication Codes', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'CONFIGURE_RECOVERY_AUTHN_CODES', 130);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('81cc968e-f8eb-4249-9ee8-49399157d347', 'webauthn-register', 'Webauthn Register', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'webauthn-register', 80);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('b573a46a-0cce-45ab-9f44-1eb03a462331', 'webauthn-register-passwordless', 'Webauthn Register Passwordless', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'webauthn-register-passwordless', 90);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('f5fa2b56-7f0b-486a-a0b0-8f7de1c47d8c', 'VERIFY_PROFILE', 'Verify Profile', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'VERIFY_PROFILE', 100);
INSERT INTO keycloak.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) VALUES ('834c04d4-9acb-4597-beef-579f54fa0989', 'idp_link', 'Linking Identity Provider', '6b03f9aa-9012-46b3-a691-480d464101db', true, false, 'idp_link', 120);


--
-- Data for Name: resource_server_resource; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_policy; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_server_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_server_perm_ticket; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: resource_uris; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: revoked_token; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: role_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: scope_mapping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.scope_mapping (client_id, role_id) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'df575729-d8d6-4b2c-a925-4f5aadc0136b');
INSERT INTO keycloak.scope_mapping (client_id, role_id) VALUES ('d8f91de3-502b-4561-89b7-ee7dc8ac8b64', 'a0765113-d540-41c0-bee1-e7a1766903fe');
INSERT INTO keycloak.scope_mapping (client_id, role_id) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '8ab6958f-237f-4dee-b793-915d02b7a279');
INSERT INTO keycloak.scope_mapping (client_id, role_id) VALUES ('b95dd4dd-8d21-4040-873f-7788a96780ce', '33f73a3e-d8fd-42ce-81b7-0dfe1610a708');


--
-- Data for Name: scope_policy; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: server_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_attribute; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.user_attribute (name, value, user_id, id, long_value_hash, long_value_hash_lower_case, long_value) VALUES ('is_temporary_admin', 'true', '95dcda34-2f55-4380-ac6d-f93310f1b321', '9490bcb2-5da4-43c6-8592-f85d89f4b8c8', NULL, NULL, NULL);
INSERT INTO keycloak.user_attribute (name, value, user_id, id, long_value_hash, long_value_hash_lower_case, long_value) VALUES ('locale', 'ru', '3bb41863-a1b5-43ef-afa0-5fcc60705a0a', '9ac431fe-4eb1-4db2-bc23-853a794685df', NULL, NULL, NULL);


--
-- Data for Name: user_consent; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_consent_client_scope; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_federation_provider; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_federation_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_federation_mapper; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_federation_mapper_config; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_group_membership; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: user_required_action; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.user_required_action (user_id, required_action) VALUES ('e9e4fb07-0e48-4f22-a6a3-b35b58867790', 'VERIFY_EMAIL');
INSERT INTO keycloak.user_required_action (user_id, required_action) VALUES ('aec8c936-b373-418e-b8d1-881816ea4d6e', 'VERIFY_EMAIL');
INSERT INTO keycloak.user_required_action (user_id, required_action) VALUES ('1b3d4a9f-286a-4a24-bc61-8d108056a8f5', 'VERIFY_EMAIL');


--
-- Data for Name: user_role_mapping; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('f5cec55e-0e1e-4e0e-83c4-5005b0e44017', '95dcda34-2f55-4380-ac6d-f93310f1b321');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('c2b96344-e43c-492b-bbee-bd65d07c8c5e', '95dcda34-2f55-4380-ac6d-f93310f1b321');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '8387b32f-8c69-4bfe-af70-c2e7d3ab1f8a');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'e9e4fb07-0e48-4f22-a6a3-b35b58867790');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'aec8c936-b373-418e-b8d1-881816ea4d6e');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'a83f5fc4-854f-474c-8bec-987472947829');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '494b0122-d3b6-4ebb-9cfc-562171927895');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '1b3d4a9f-286a-4a24-bc61-8d108056a8f5');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '2310266d-d483-463d-a2e5-848730825fde');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '8c72e4b5-3f3e-4ea0-aec2-036482068f8c');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '39ecb97c-14f2-43c9-98c3-a1c40fe6685d');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'f008897a-c12a-45ee-943d-2effec955a51');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '01392bd1-15c8-4493-9a27-762dbbd988e1');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'c3a9f123-fa66-4491-9e63-8e14b7b86653');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'cbce803f-4227-4c08-99dc-66dacc43cfae');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', '3bb41863-a1b5-43ef-afa0-5fcc60705a0a');
INSERT INTO keycloak.user_role_mapping (role_id, user_id) VALUES ('1a9bdb6b-ef2b-4661-8543-62561be47aff', 'b70b54cf-97a6-46c5-aebc-970dfcf0f928');


--
-- Data for Name: web_origins; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--

INSERT INTO keycloak.web_origins (client_id, value) VALUES ('6126224e-eca8-41cf-bebe-da15f56c0111', '+');
INSERT INTO keycloak.web_origins (client_id, value) VALUES ('775ebc9e-a65c-4635-8bfe-01b7c02a581b', '+');
INSERT INTO keycloak.web_origins (client_id, value) VALUES ('ad353a5e-ecaa-4314-87c1-292e71b8282c', 'https://app.acom-offer-desk.ru');


--
-- Data for Name: workflow_state; Type: TABLE DATA; Schema: keycloak; Owner: order_admin
--



--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.roles (id, role) VALUES (1, 'Суперадмин');
INSERT INTO public.roles (id, role) VALUES (2, 'Администратор');
INSERT INTO public.roles (id, role) VALUES (3, 'Контрагент');
INSERT INTO public.roles (id, role) VALUES (4, 'Руководитель Проекта');
INSERT INTO public.roles (id, role) VALUES (5, 'Ведущий экономист');
INSERT INTO public.roles (id, role) VALUES (6, 'Экономист');
INSERT INTO public.roles (id, role) VALUES (7, 'Оператор');
INSERT INTO public.roles (id, role) VALUES (8, 'СБ');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('superadmin', 1, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('AErmoshkin', 4, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('FedorErmoshkin', 4, NULL, 'inactive', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('MHlistenkov', 5, 'FedorErmoshkin', 'inactive', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('VKhlistun', 2, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('DDlatypov', 5, 'AErmoshkin', 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('ASosipova', 3, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('Контрагент 1', 3, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('Danilkaa', 6, 'MHlistenkov', 'active', '2026-04-23 17:05:21.181534', '2026-04-23 17:05:21.181534');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('Danilka', 6, 'MHlistenkov', 'blacklist', '2026-04-23 17:03:02.529259', '2026-04-23 17:05:36.60033');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('baklazhka_23_04', 3, NULL, 'active', '2026-04-23 17:08:43.744241', '2026-04-23 17:08:43.744241');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('DLatypov', 3, NULL, 'active', '2026-04-13 11:13:49.022218', '2026-04-23 17:25:35.674596');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('FEErmoshkin', 2, NULL, 'inactive', '2026-04-23 17:49:46.670552', '2026-04-23 17:50:33.044208');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('FFErmoshkin', 4, NULL, 'active', '2026-04-23 17:51:05.444221', '2026-04-23 17:51:05.444221');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('AnGrakhova', 7, NULL, 'active', '2026-04-23 17:52:11.401401', '2026-04-23 17:52:11.401401');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('ip_grahova_anastasiya_andreevna_23_04', 3, NULL, 'active', '2026-04-23 17:54:56.062783', '2026-04-23 17:54:56.062783');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('project_manager', 4, NULL, 'active', '2026-04-24 10:42:35.424106', '2026-04-24 10:42:35.424106');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('auto_rp_e2e_20260424', 4, NULL, 'active', '2026-04-24 16:44:56.245273', '2026-04-24 16:44:56.245273');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('auto_ve_e2e_20260424', 5, 'auto_rp_e2e_20260424', 'active', '2026-04-24 16:47:11.24879', '2026-04-24 16:47:11.24879');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('auto_ek_e2e_20260424', 4, 'auto_ve_e2e_20260424', 'active', '2026-04-24 16:47:52.694908', '2026-04-27 16:22:07.445053');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('vvv', 4, NULL, 'active', '2026-04-27 16:26:31.889369', '2026-04-27 16:26:31.889369');
INSERT INTO public.users (id, id_role, id_parent, status, created_at, updated_at) VALUES ('lead_economist', 5, 'project_manager', 'active', '2026-05-05 10:13:26.858134', '2026-05-05 10:13:26.858134');


--
-- Data for Name: economy_plans; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.economy_plans (id, id_parent_plan, name, id_user, id_parent_user_snapshot, period_start, period_end, plan_amount, fact_amount, created_at, updated_at) VALUES (1, NULL, 'zzzz', 'project_manager', NULL, '2026-05-01', '2026-05-31', 1000000.00, NULL, '2026-05-05 10:10:00.27074', '2026-05-05 10:10:00.27074');


--
-- Data for Name: requests; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (14, NULL, 'review', '2026-04-06 23:59:59', '2026-04-06 16:52:04.593606', NULL, NULL, 'superadmin', 3425465.00, NULL, '2026-04-07 03:01:00.025093', NULL);
INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (15, 'Закупка щебня', 'closed', '2026-04-07 23:59:59', '2026-04-06 17:02:59.873874', '2026-04-07 07:34:05.263769', 1, 'superadmin', 300000.00, 250000.00, '2026-04-07 10:34:05.262804', NULL);
INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (16, NULL, 'review', '2026-04-07 23:59:59', '2026-04-07 10:30:09.873978', NULL, NULL, 'superadmin', 60000000.00, NULL, '2026-04-08 03:01:00.010984', NULL);
INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (18, 'Тест', 'review', '2026-04-24 23:59:59', '2026-04-24 16:38:01.605604', NULL, NULL, 'superadmin', 11111.00, NULL, '2026-04-25 03:01:00.023361', NULL);
INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (17, 'электроника', 'review', '2026-04-27 23:59:59', '2026-04-07 10:38:38.869972', NULL, NULL, 'superadmin', 4456545.00, NULL, '2026-04-28 03:01:00.020256', NULL);
INSERT INTO public.requests (id, description, status, deadline_at, created_at, closed_at, id_offer, id_user, initial_amount, final_amount, updated_at, id_plan) VALUES (19, 'vvvv', 'review', '2026-04-27 23:59:59', '2026-04-27 16:23:59.587745', NULL, NULL, 'superadmin', 111.00, NULL, '2026-04-28 03:01:00.020256', NULL);


--
-- Data for Name: offers; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.offers (id, id_request, id_user, status, offer_amount, created_at, updated_at) VALUES (1, 15, 'ASosipova', 'accepted', 250000.00, '2026-04-06 17:10:15.006917', '2026-04-07 10:31:56.452567');
INSERT INTO public.offers (id, id_request, id_user, status, offer_amount, created_at, updated_at) VALUES (2, 16, 'Контрагент 1', 'accepted', 5000000.00, '2026-04-07 10:35:51.286706', '2026-04-07 10:37:40.191137');
INSERT INTO public.offers (id, id_request, id_user, status, offer_amount, created_at, updated_at) VALUES (4, 17, 'ip_grahova_anastasiya_andreevna_23_04', 'submitted', 4300000.00, '2026-04-23 18:01:50.124862', '2026-04-23 18:01:50.124862');


--
-- Data for Name: chats; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.chats (id, last_message_id, last_message_at) VALUES (1, 2, '2026-04-07 10:31:38.998191');
INSERT INTO public.chats (id, last_message_id, last_message_at) VALUES (2, NULL, '2026-04-07 10:35:51.286706');
INSERT INTO public.chats (id, last_message_id, last_message_at) VALUES (4, NULL, '2026-04-23 18:01:50.124862');


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.messages (id, id_chat, id_user, text, type, reply_to_id, created_at, updated_at) VALUES (1, 1, 'ASosipova', 'здравствуйте, какие условия оплаты', 'text', NULL, '2026-04-06 17:11:34.033866', '2026-04-06 17:11:34.033866');
INSERT INTO public.messages (id, id_chat, id_user, text, type, reply_to_id, created_at, updated_at) VALUES (2, 1, 'superadmin', 'здравствуйте, постоплата 100%', 'text', NULL, '2026-04-07 10:31:38.998191', '2026-04-07 10:31:38.998191');


--
-- Data for Name: chat_participants; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (1, 'ASosipova', '2026-04-06 17:10:15.006917', NULL, NULL, '2026-04-06 17:10:15.006917', false, false);
INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (1, 'superadmin', '2026-04-06 17:10:15.006917', NULL, 1, '2026-04-07 10:31:10.759316', false, false);
INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (2, 'Контрагент 1', '2026-04-07 10:35:51.286706', NULL, NULL, '2026-04-07 10:35:51.286706', false, false);
INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (2, 'superadmin', '2026-04-07 10:35:51.286706', NULL, NULL, '2026-04-07 10:35:51.286706', false, false);
INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (4, 'ip_grahova_anastasiya_andreevna_23_04', '2026-04-23 18:01:50.124862', NULL, NULL, '2026-04-23 18:01:50.124862', false, false);
INSERT INTO public.chat_participants (id_chat, id_user, joined_at, left_at, last_read_message_id, last_read_at, is_muted, is_archived) VALUES (4, 'superadmin', '2026-04-23 18:01:50.124862', NULL, NULL, '2026-04-23 18:01:50.124862', false, false);


--
-- Data for Name: company_contacts; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.company_contacts (id, company_name, inn, phone, mail, address, note) VALUES ('DLatypov', 'Меркатор', '7709401982', '89907393930', 'Hsjsbsjzj@mail.ru', '123001, г. Москва, пер. Мамоновский, д. 4, стр. 1, эт/пом/ком 2/iii/3', 'Контрагент');
INSERT INTO public.company_contacts (id, company_name, inn, phone, mail, address, note) VALUES ('Контрагент 1', 'Контрагент', '829299202928', '89999999999', 'ivanov@gmail.com', 'г. Москва, ул. Садовая, 1', 'Поставщик электроники');
INSERT INTO public.company_contacts (id, company_name, inn, phone, mail, address, note) VALUES ('baklazhka_23_04', 'Баклажка', '1234567890', '+7 (565) 598-74-45', 'annaosipova567@gmail.com', 'г.Москва, улица Коненкова, дом 3', 'Создание контрагента через суперадмина с подтверждением почты');
INSERT INTO public.company_contacts (id, company_name, inn, phone, mail, address, note) VALUES ('ip_grahova_anastasiya_andreevna_23_04', 'ИП Грахова Анастасия Андреевна', '345678990901', '+7 (945) 637-84-95', 'ngrakhova@vk.com', 'Нефтяников 150', 'Не указано');


--
-- Data for Name: economy_plan_request_facts; Type: TABLE DATA; Schema: public; Owner: order_admin
--



--
-- Data for Name: feed_back; Type: TABLE DATA; Schema: public; Owner: order_admin
--



--
-- Data for Name: storage_objects; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (1, 'acom-offer-desk', 'objects/e39843663906eba470c8c7c05684fb329a43b8443e0f69c1ff1936f38d727618', 'e39843663906eba470c8c7c05684fb329a43b8443e0f69c1ff1936f38d727618', 'image/jpeg', 99563);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (2, 'acom-offer-desk', 'objects/0b6ae3f16f01f13ca97706354f8625e2585345b76fa1e93f70d2742ec283a91d', '0b6ae3f16f01f13ca97706354f8625e2585345b76fa1e93f70d2742ec283a91d', 'image/png', 44512);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (3, 'acom-offer-desk', 'objects/64e8b35ffd172707ac62e92121df1cbfa58372826a9ba932b79e7e89c738e2e8', '64e8b35ffd172707ac62e92121df1cbfa58372826a9ba932b79e7e89c738e2e8', 'application/pdf', 194993);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (4, 'acom-offer-desk', 'objects/ad68e9807ecc18597a6d9567a963e5ea08f48efeeec58800d942b505f15f173d', 'ad68e9807ecc18597a6d9567a963e5ea08f48efeeec58800d942b505f15f173d', 'application/pdf', 915143);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (5, 'acom-offer-desk', 'objects/c6553526ac641c85807808259cddd599ee3ab372a7df2c5a04838f9c25a9006e', 'c6553526ac641c85807808259cddd599ee3ab372a7df2c5a04838f9c25a9006e', 'application/pdf', 300859);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (6, 'acom-offer-desk', 'objects/5cdaa17739406ba9766551097f726b67ae95e1ee4a2f3b8caefc4aa91cf47107', '5cdaa17739406ba9766551097f726b67ae95e1ee4a2f3b8caefc4aa91cf47107', 'image/jpeg', 54273);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (7, 'acom-offer-desk', 'objects/ce8c23593fbe40a38fb713e2ca4e6f086cbe1ed0651b8f27e3244bc2e97ab681', 'ce8c23593fbe40a38fb713e2ca4e6f086cbe1ed0651b8f27e3244bc2e97ab681', 'application/pdf', 776419);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (8, 'acom-offer-desk', 'objects/858cd949a58cf8b3b955bf395d5bbbe283d7a66f479172b2ccc1ec8173a01923', '858cd949a58cf8b3b955bf395d5bbbe283d7a66f479172b2ccc1ec8173a01923', 'text/markdown', 28566);
INSERT INTO public.storage_objects (id, storage_bucket, storage_key, content_sha256, mime_type, size_bytes) VALUES (9, 'acom-offer-desk', 'objects/b5431457fe09750feb6f1915557a138ac4c1f671aef07dde61d94b70f78fe5c5', 'b5431457fe09750feb6f1915557a138ac4c1f671aef07dde61d94b70f78fe5c5', 'image/png', 25001);


--
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (1, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-03 10:39:43.240858');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (2, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-06 16:52:04.593606');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (3, 2, 'logo-001.png', '2026-04-06 16:52:04.593606');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (4, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-06 17:02:59.873874');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (5, 1, 'тз щебня.jpg', '2026-04-06 17:02:59.873874');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (6, 3, 'КП изд. Волна-2  24шт от 31.03.2026.pdf', '2026-04-06 17:10:32.371075');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (7, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-07 10:30:09.873978');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (8, 4, 'ТЗ.pdf', '2026-04-07 10:30:09.873978');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (9, 5, 'КП 3.pdf', '2026-04-07 10:36:11.921997');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (10, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-07 10:38:38.869972');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (11, 4, 'ТЗ.pdf', '2026-04-07 10:38:38.869972');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (12, 6, 'photo_2026-04-02_10-08-56.jpg', '2026-04-13 15:11:25.792691');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (13, 7, 'КП источники актуал.pdf', '2026-04-23 18:01:50.124862');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (14, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-24 16:38:01.605604');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (15, 8, 'FIXES_APPLIED.md', '2026-04-24 16:38:01.605604');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (16, 1, 'Alabuga_SEZ_Logo.jpg', '2026-04-27 16:23:59.587745');
INSERT INTO public.files (id, id_storage_object, original_name, created_at) VALUES (17, 9, 'Снимок экрана от 2026-01-19 10-28-11.png', '2026-04-27 16:23:59.587745');


--
-- Data for Name: flyway_schema_history; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.flyway_schema_history (installed_rank, version, description, type, script, checksum, installed_by, installed_on, execution_time, success) VALUES (1, '1.0.0', 'baseline_from_init_scripts', 'BASELINE', 'baseline_from_init_scripts', NULL, 'order_admin', '2026-03-31 12:57:56.517021', 0, true);
INSERT INTO public.flyway_schema_history (installed_rank, version, description, type, script, checksum, installed_by, installed_on, execution_time, success) VALUES (2, '1.0.1', 'iam keycloak contacts unified', 'SQL', 'V1.0.1__iam_keycloak_contacts_unified.sql', 321931001, 'order_admin', '2026-04-13 11:13:48.929309', 136, true);
INSERT INTO public.flyway_schema_history (installed_rank, version, description, type, script, checksum, installed_by, installed_on, execution_time, success) VALUES (3, '1.0.2', 'add economy plans', 'SQL', 'V1.0.2__add_economy_plans.sql', 1199660754, 'order_admin', '2026-05-05 06:52:02.213382', 73, true);


--
-- Data for Name: message_files; Type: TABLE DATA; Schema: public; Owner: order_admin
--



--
-- Data for Name: message_receipts; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.message_receipts (id_message, id_user, delivered_at, read_at) VALUES (1, 'superadmin', '2026-04-07 10:30:26.628127', '2026-04-07 10:31:10.759316');
INSERT INTO public.message_receipts (id_message, id_user, delivered_at, read_at) VALUES (2, 'ASosipova', NULL, NULL);


--
-- Data for Name: normative_files; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.normative_files (id, id_file) VALUES (1, 1);


--
-- Data for Name: offer_files; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.offer_files (id, id_offer) VALUES (6, 1);
INSERT INTO public.offer_files (id, id_offer) VALUES (9, 2);
INSERT INTO public.offer_files (id, id_offer) VALUES (13, 4);


--
-- Data for Name: profiles; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('DLatypov', 'Латыпов Даниил Русланович', '89059199101', 'Latypov_20200@mail.ru');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('MHlistenkov', 'Хлыстенков Михаил Олегович', '89393939993', 'Не указано');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('AErmoshkin', 'Ермошкин Фёдор Андреевич', '89059199101', 'Не указано');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('Контрагент 1', 'Иванов Иван Иванович', '8-999-899-66-77', 'Не указано');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('superadmin', 'Bootstrap Superadmin', 'Не указано', 'superadmin@local.invalid');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('Danilka', 'Не указано', 'Не указано', 'Danilka@gmail.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('Danilkaa', 'Не указано', 'Не указано', 'latypov_20200@mail.ru');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('baklazhka_23_04', 'Не указано', 'Не указано', 'Не указано');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('FEErmoshkin', 'Не указано', 'Не указано', 'latypov_2020@mail.ru');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('FFErmoshkin', 'Не указано', 'Не указано', 'FFErmoshkin@mail.ru');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('AnGrakhova', 'Не указано', 'Не указано', 'AnGrakhova@alabuga.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('ip_grahova_anastasiya_andreevna_23_04', 'Анастасия Грахова', 'Не указано', 'ngrakhova@vk.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('project_manager', 'Руководитель Проекта', 'Не указано', 'alexandrasmirnova230903@gmail.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('auto_rp_e2e_20260424', 'Не указано', 'Не указано', 'zvezda.smerti148+rp_e2e@gmail.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('auto_ve_e2e_20260424', 'Не указано', 'Не указано', 'zvezda.smerti148+ve_e2e@gmail.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('auto_ek_e2e_20260424', 'Не указано', 'Не указано', 'zvezda.smerti148@gmail.com');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('vvv', 'ddddd ddddd', 'Не указано', 'sin.svaroga@mail.ru');
INSERT INTO public.profiles (id, full_name, phone, mail) VALUES ('lead_economist', 'Андрей Иванов', 'Не указано', 'hijewop375@iapapi.com');


--
-- Data for Name: request_files; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.request_files (id, id_request) VALUES (2, 14);
INSERT INTO public.request_files (id, id_request) VALUES (3, 14);
INSERT INTO public.request_files (id, id_request) VALUES (4, 15);
INSERT INTO public.request_files (id, id_request) VALUES (5, 15);
INSERT INTO public.request_files (id, id_request) VALUES (7, 16);
INSERT INTO public.request_files (id, id_request) VALUES (8, 16);
INSERT INTO public.request_files (id, id_request) VALUES (10, 17);
INSERT INTO public.request_files (id, id_request) VALUES (11, 17);
INSERT INTO public.request_files (id, id_request) VALUES (14, 18);
INSERT INTO public.request_files (id, id_request) VALUES (15, 18);
INSERT INTO public.request_files (id, id_request) VALUES (16, 19);
INSERT INTO public.request_files (id, id_request) VALUES (17, 19);


--
-- Data for Name: request_hidden_contractors; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.request_hidden_contractors (id_request, id_user) VALUES (16, 'ASosipova');
INSERT INTO public.request_hidden_contractors (id_request, id_user) VALUES (17, 'Контрагент 1');


--
-- Data for Name: request_offer_stats; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (14, 0, 0, 0, 0, '2026-04-06 16:52:04.593606');
INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (15, 0, 0, 1, 0, '2026-04-07 10:31:05.853035');
INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (16, 0, 0, 1, 0, '2026-04-07 10:37:40.191137');
INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (17, 2, 0, 0, 0, '2026-04-23 18:01:50.124862');
INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (18, 0, 0, 0, 0, '2026-04-24 16:38:01.605604');
INSERT INTO public.request_offer_stats (request_id, count_submitted, count_deleted_alert, count_accepted_total, count_rejected_total, updated_at) VALUES (19, 0, 0, 0, 0, '2026-04-27 16:23:59.587745');


--
-- Data for Name: user_auth_accounts; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (2, 'Контрагент 1', 'telegram', '473169262', NULL, NULL, true, '2026-04-13 11:13:49.022218', NULL);
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (11, 'vvv', 'keycloak', 'c3a9f123-fa66-4491-9e63-8e14b7b86653', 'vvv', 'sin.svaroga@mail.ru', true, '2026-04-27 16:28:46.359374', '2026-04-27 20:09:07.400954');
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (10, 'project_manager', 'keycloak', '39ecb97c-14f2-43c9-98c3-a1c40fe6685d', 'project_manager', 'alexandrasmirnova230903@gmail.com', true, '2026-04-24 10:44:24.923127', '2026-05-05 09:11:04.909247');
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (9, 'ip_grahova_anastasiya_andreevna_23_04', 'keycloak', '8c72e4b5-3f3e-4ea0-aec2-036482068f8c', 'ip_grahova_anastasiya_andreevna_23_04', 'ngrakhova@vk.com', true, '2026-04-23 17:57:28.828912', '2026-04-23 15:13:52.325613');
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (1, 'DLatypov', 'telegram', '5227207692', NULL, NULL, true, '2026-04-13 11:13:49.022218', NULL);
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (13, 'lead_economist', 'keycloak', 'b70b54cf-97a6-46c5-aebc-970dfcf0f928', 'lead_economist', 'hijewop375@iapapi.com', true, '2026-05-05 10:13:26.858134', '2026-05-05 07:15:12.307388');
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (12, 'auto_ek_e2e_20260424', 'keycloak', 'cbce803f-4227-4c08-99dc-66dacc43cfae', 'auto_ek_e2e_20260424', 'zvezda.smerti148@gmail.com', true, '2026-04-27 16:35:55.336817', NULL);
INSERT INTO public.user_auth_accounts (id, id_user, provider, external_subject_id, external_username, external_email, is_active, linked_at, last_login_at) VALUES (3, 'superadmin', 'keycloak', '8387b32f-8c69-4bfe-af70-c2e7d3ab1f8a', 'superadmin', 'superadmin@local.invalid', true, '2026-04-13 14:14:52.308962', '2026-05-08 06:46:46.889217');


--
-- Data for Name: user_contact_channels; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (2, 'Контрагент 1', 'telegram', '473169262', true, '2026-04-13 11:13:49.022218', true, true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (3, 'DLatypov', 'email', 'Latypov_20200@mail.ru', false, NULL, true, true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (4, 'superadmin', 'email', 'superadmin@local.invalid', true, '2026-05-08 06:46:46.891971', true, true, '2026-04-13 14:14:52.308962', '2026-05-08 09:46:46.886754');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (1, 'DLatypov', 'telegram', '5227207692', true, '2026-04-23 14:25:35.680628', true, true, '2026-04-13 11:13:49.022218', '2026-04-23 17:25:35.674596');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (10, 'ip_grahova_anastasiya_andreevna_23_04', 'email', 'ngrakhova@vk.com', true, '2026-04-23 15:13:52.327424', true, true, '2026-04-23 17:57:28.828912', '2026-04-23 18:13:52.323111');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (13, 'lead_economist', 'email', 'hijewop375@iapapi.com', true, '2026-05-05 07:15:12.308557', true, true, '2026-05-05 10:15:06.112258', '2026-05-05 10:15:12.30577');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (11, 'project_manager', 'email', 'alexandrasmirnova230903@gmail.com', true, '2026-05-05 09:11:04.911295', true, true, '2026-04-24 10:44:24.923127', '2026-05-05 12:11:04.906763');
INSERT INTO public.user_contact_channels (id, id_user, channel_type, channel_value, is_verified, verified_at, is_primary, is_active, created_at, updated_at) VALUES (12, 'vvv', 'email', 'sin.svaroga@mail.ru', true, '2026-04-27 20:09:07.402262', true, true, '2026-04-27 16:28:46.359374', '2026-04-27 23:09:07.394662');


--
-- Data for Name: user_notification_preferences; Type: TABLE DATA; Schema: public; Owner: order_admin
--

INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (1, 1, 'chat', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (2, 1, 'request', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (3, 1, 'offer', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (4, 1, 'system', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (5, 2, 'chat', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (6, 2, 'request', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (7, 2, 'offer', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (8, 2, 'system', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (9, 3, 'chat', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (10, 3, 'request', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (11, 3, 'offer', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');
INSERT INTO public.user_notification_preferences (id, id_contact_channel, notification_type, is_enabled, created_at, updated_at) VALUES (12, 3, 'system', true, '2026-04-13 11:13:49.022218', '2026-04-13 11:13:49.022218');


--
-- Data for Name: user_status_periods; Type: TABLE DATA; Schema: public; Owner: order_admin
--



--
-- Name: jobid_seq; Type: SEQUENCE SET; Schema: cron; Owner: order_admin
--

SELECT pg_catalog.setval('cron.jobid_seq', 1, true);


--
-- Name: runid_seq; Type: SEQUENCE SET; Schema: cron; Owner: order_admin
--

SELECT pg_catalog.setval('cron.runid_seq', 41, true);


--
-- Name: economy_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.economy_plans_id_seq', 1, true);


--
-- Name: feed_back_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.feed_back_id_seq', 1, false);


--
-- Name: files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.files_id_seq', 17, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.messages_id_seq', 2, true);


--
-- Name: offers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.offers_id_seq', 4, true);


--
-- Name: requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.requests_id_seq', 19, true);


--
-- Name: storage_objects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.storage_objects_id_seq', 9, true);


--
-- Name: user_auth_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.user_auth_accounts_id_seq', 13, true);


--
-- Name: user_contact_channels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.user_contact_channels_id_seq', 13, true);


--
-- Name: user_notification_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.user_notification_preferences_id_seq', 12, true);


--
-- Name: user_status_periods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: order_admin
--

SELECT pg_catalog.setval('public.user_status_periods_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict zWlfAqg2bNMLaw4u35il6ZvAOWL38AV6PkQPP7rhniXV6Qon8fhQbQaGAYV7N4B

