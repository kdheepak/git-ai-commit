# Default recipe calls commit
default: commit

# Pass all arguments directly to git-copilot-commit
commit *args:
    uv run git-copilot-commit commit {{args}}


# Bump version based on GitHub tags and create empty commit
bump type="patch":
    #!/usr/bin/env bash
    set -euo pipefail

    # Get the latest tag from GitHub
    echo "Fetching latest tag from GitHub..."
    latest_tag=$(gh release list --limit 1 --json tagName --jq '.[0].tagName // "v0.0.0"')

    # Remove 'v' prefix if present
    version=${latest_tag#v}

    # Parse version components
    IFS='.' read -r major minor patch <<< "$version"

    # Bump based on type
    case "{{type}}" in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo "Error: Invalid bump type '{{type}}'. Use: major, minor, or patch"
            exit 1
            ;;
    esac

    # Create new version
    new_version="v${major}.${minor}.${patch}"

    echo "Current version: $latest_tag"
    echo "New version: $new_version"

    # Create empty commit
    git commit --allow-empty -m "Bump version to $new_version"

    echo "✓ Created empty commit for $new_version"
    echo "  Next: Create and push tag with: git tag $new_version && git push && git push --tags"
