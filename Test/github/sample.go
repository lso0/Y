package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/google/go-github/v60/github"
	"github.com/joho/godotenv"
	"golang.org/x/oauth2"
)

type Repository struct {
	FullName    string `json:"full_name"`
	Description string `json:"description"`
	URL         string `json:"url"`
}

type List struct {
	Name         string       `json:"name"`
	Description  string       `json:"description"`
	Repositories []Repository `json:"repositories"`
}

type ListsFile struct {
	Lists []List `json:"lists"`
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		log.Fatal("Please set GITHUB_TOKEN environment variable")
	}
	fmt.Printf("Token length: %d\n", len(token))

	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)
	client := github.NewClient(tc)

	// Print authenticated user
	authUser, _, err := client.Users.Get(ctx, "")
	if err != nil {
		log.Fatalf("Failed to get authenticated user: %v", err)
	}
	fmt.Printf("Authenticated as: %s\n", authUser.GetLogin())

	// List starred repositories (first page only for debug)
	opts := &github.ActivityListStarredOptions{
		ListOptions: github.ListOptions{PerPage: 100},
	}
	stars, resp, err := client.Activity.ListStarred(ctx, "", opts)
	if err != nil {
		log.Printf("Error fetching stars: %v\n", err)
		if resp != nil {
			log.Printf("Response status: %s\n", resp.Status)
		}
		log.Fatal(err)
	}
	fmt.Printf("Number of starred repos in first page: %d\n", len(stars))
	if len(stars) > 0 && stars[0].Repository != nil {
		fmt.Printf("First starred repo: %s\n", stars[0].Repository.GetFullName())
	}

	// Print total count (old logic, but will be 0 if nothing fetched)
	var allStars []*github.StarredRepository
	allStars = append(allStars, stars...)
	for resp != nil && resp.NextPage != 0 {
		opts.Page = resp.NextPage
		stars, resp, err = client.Activity.ListStarred(ctx, "", opts)
		if err != nil {
			log.Fatal(err)
		}
		allStars = append(allStars, stars...)
	}
	fmt.Printf("Total starred repositories: %d\n\n", len(allStars))

	fmt.Println("First 10 starred repositories:")
	fmt.Println("----------------------------")
	for i, star := range allStars[:min(10, len(allStars))] {
		if star == nil || star.Repository == nil {
			continue
		}
		repo := star.Repository
		fmt.Printf("%d. %s\n", i+1, repo.GetFullName())
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func getStringValue(s *string) string {
	if s != nil {
		return *s
	}
	return ""
}
