SELECT
    events.type AS type,
    repos.repository_url AS repository_url,
    events.actor AS actor
  FROM (
    SELECT
        repository_url,
        COUNT(repository_url) AS stars
      FROM [githubarchive:github.timeline]
      WHERE type="WatchEvent"
      GROUP EACH BY repository_url
      ORDER BY stars DESC
      LIMIT 100
  ) AS repos
  JOIN EACH [githubarchive:github.timeline] AS events
  ON repos.repository_url = events.repository_url
  WHERE
    type="PushEvent"
  GROUP EACH BY type, repository_url, actor
