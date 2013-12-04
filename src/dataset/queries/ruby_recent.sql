SELECT type, repository_url, actor
  FROM [githubarchive:github.timeline]
  WHERE
    type="PushEvent"
    AND PARSE_UTC_USEC(created_at) >= PARSE_UTC_USEC("2013-11-01 00:00:00")
    AND PARSE_UTC_USEC(created_at) < PARSE_UTC_USEC("2013-12-01 00:00:00")
    AND repository_language="Ruby"
  GROUP EACH BY type, repository_url, actor
