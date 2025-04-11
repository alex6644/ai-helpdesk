CREATE TABLE email_queue (
    id UUID PRIMARY KEY,
    sender TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    date_received TIMESTAMP NOT NULL,
    status TEXT NOT NULL
);
