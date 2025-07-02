package main

import (
	"context"
	"fmt"
	"os"

	"github.com/google/go-github/v60/github"
	"github.com/joho/godotenv"
	"golang.org/x/oauth2"
)

type GitHubClient struct {
	client *github.Client
	ctx    context.Context
}

type Repository struct {
	FullName    string `json:"full_name"`
	Description string `json:"description"`
	URL         string `json:"url"`
	Stars       int    `json:"stars"`
}

func NewGitHubClient() (*GitHubClient, error) {
	// Try to load .env file (optional)
	_ = godotenv.Load()

	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		return nil, fmt.Errorf("GITHUB_TOKEN environment variable not set")
	}

	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)
	client := github.NewClient(tc)

	return &GitHubClient{
		client: client,
		ctx:    ctx,
	}, nil
}

func (g *GitHubClient) GetAuthenticatedUser() (string, error) {
	user, _, err := g.client.Users.Get(g.ctx, "")
	if err != nil {
		return "", err
	}
	return user.GetLogin(), nil
}

func (g *GitHubClient) GetStarredRepos(limit int) ([]Repository, error) {
	opts := &github.ActivityListStarredOptions{
		ListOptions: github.ListOptions{PerPage: limit},
	}

	stars, _, err := g.client.Activity.ListStarred(g.ctx, "", opts)
	if err != nil {
		return nil, err
	}

	var repos []Repository
	for _, star := range stars {
		if star.Repository != nil {
			repo := Repository{
				FullName:    star.Repository.GetFullName(),
				Description: star.Repository.GetDescription(),
				URL:         star.Repository.GetHTMLURL(),
				Stars:       star.Repository.GetStargazersCount(),
			}
			repos = append(repos, repo)
		}
	}

	return repos, nil
}

func (g *GitHubClient) GetUserRepos(limit int) ([]Repository, error) {
	opts := &github.RepositoryListOptions{
		Type:        "owner",
		ListOptions: github.ListOptions{PerPage: limit},
	}

	repoList, _, err := g.client.Repositories.List(g.ctx, "", opts)
	if err != nil {
		return nil, err
	}

	var repos []Repository
	for _, repo := range repoList {
		if repo != nil {
			repository := Repository{
				FullName:    repo.GetFullName(),
				Description: repo.GetDescription(),
				URL:         repo.GetHTMLURL(),
				Stars:       repo.GetStargazersCount(),
			}
			repos = append(repos, repository)
		}
	}

	return repos, nil
}
