SELECT
    events.type AS type,
    repos.repository_url AS repository_url,
    events.actor AS actor
  FROM (
    SELECT
      repository_url,
      COUNT(DISTINCT actor) as users
    FROM [githubarchive:github.timeline]
    WHERE
      type="PushEvent"
      AND PARSE_UTC_USEC(created_at) >= PARSE_UTC_USEC('2012-01-01 00:00:00')
    GROUP EACH BY repository_url
    ORDER BY users DESC
    LIMIT 100
  ) AS repos
  JOIN EACH [githubarchive:github.timeline] AS events
  ON repos.repository_url = events.repository_url
  WHERE
    type="PushEvent"
  GROUP EACH BY type, repository_url, actor
