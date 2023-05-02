CREATE TABLE source
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "url" TEXT NOT NULL,
  status_code INT NOT NULL,
  status_msg TEXT
);

CREATE TABLE video_chunk
(
  id SERIAL PRIMARY KEY,
  file_path TEXT NOT NULL,
  start_time FLOAT NOT NULL,
  end_time FLOAT NOT NULL,
  source_id INT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source(id)
);