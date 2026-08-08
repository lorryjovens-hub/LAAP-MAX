import { useEffect, useState } from 'react';

export function useGitHubStars(repo: string) {
  const [stars, setStars] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch(`https://api.github.com/repos/${repo}`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled && typeof data?.stargazers_count === 'number') {
          setStars(data.stargazers_count);
        }
      })
      .catch(() => {
        if (!cancelled) setStars(null);
      });

    return () => { cancelled = true; };
  }, [repo]);

  return stars;
}
