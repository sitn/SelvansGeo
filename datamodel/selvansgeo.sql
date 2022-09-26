-- Table: selvansgeo.analysis

-- DROP TABLE selvansgeo.analysis;

CREATE TABLE selvansgeo.analysis
(
  id integer NOT NULL,
  analysis_name character varying(256),
  querystring text,
  default_symbology character varying(256),
  join_target_pkfield character varying(256),
  join_source_fkfield character varying(256),
  field_of_interest character varying(256),
  join_target_table character varying(256),
  join_target_schema character varying(256),
  field_of_interest_type character varying(256),
  date_filtering boolean,
  pie_chart boolean,
  pie_chart_colors text,
  datefield character varying(256),
  timerange_filtering boolean,
  coupetype_filtering boolean,
  CONSTRAINT analysis_pkey PRIMARY KEY (id)
);