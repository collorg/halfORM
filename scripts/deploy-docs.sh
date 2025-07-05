#!/bin/bash
# scripts/deploy-docs.sh
# Local development script for managing documentation versions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy VERSION [ALIAS]  Deploy a version of the documentation"
    echo "  list                    List all deployed versions"
    echo "  serve                   Serve the documentation locally"
    echo "  set-default VERSION     Set the default version"
    echo "  delete VERSION          Delete a version"
    echo "  build                   Build current documentation"
    echo ""
    echo "Examples:"
    echo "  $0 deploy 0.16.0 latest    # Deploy version 0.16.0 as latest"
    echo "  $0 deploy dev              # Deploy development version"
    echo "  $0 set-default latest      # Set latest as default"
    echo "  $0 serve                   # Serve documentation locally"
    echo ""
}

# Function to check if mike is installed
check_mike() {
    if ! command -v mike &> /dev/null; then
        echo -e "${RED}Error: mike is not installed${NC}"
        echo "Install with: pip install mike"
        exit 1
    fi
}

# Function to deploy a version
deploy_version() {
    local version=$1
    local alias=$2
    
    if [ -z "$version" ]; then
        echo -e "${RED}Error: Version is required${NC}"
        echo "Usage: $0 deploy VERSION [ALIAS]"
        exit 1
    fi
    
    echo -e "${YELLOW}Deploying documentation version: $version${NC}"
    
    if [ -n "$alias" ]; then
        echo -e "${YELLOW}With alias: $alias${NC}"
        mike deploy --update-aliases "$version" "$alias"
    else
        mike deploy "$version"
    fi
    
    echo -e "${GREEN}Successfully deployed version $version${NC}"
}

# Function to list versions
list_versions() {
    echo -e "${YELLOW}Deployed documentation versions:${NC}"
    mike list
}

# Function to serve documentation
serve_docs() {
    echo -e "${YELLOW}Starting documentation server...${NC}"
    echo -e "${GREEN}Documentation will be available at: http://localhost:8000${NC}"
    mike serve
}

# Function to set default version
set_default() {
    local version=$1
    
    if [ -z "$version" ]; then
        echo -e "${RED}Error: Version is required${NC}"
        echo "Usage: $0 set-default VERSION"
        exit 1
    fi
    
    echo -e "${YELLOW}Setting default version to: $version${NC}"
    mike set-default "$version"
    echo -e "${GREEN}Default version set to $version${NC}"
}

# Function to delete a version
delete_version() {
    local version=$1
    
    if [ -z "$version" ]; then
        echo -e "${RED}Error: Version is required${NC}"
        echo "Usage: $0 delete VERSION"
        exit 1
    fi
    
    echo -e "${YELLOW}Deleting version: $version${NC}"
    mike delete "$version"
    echo -e "${GREEN}Version $version deleted${NC}"
}

# Function to build documentation
build_docs() {
    echo -e "${YELLOW}Building documentation...${NC}"
    mkdocs build
    echo -e "${GREEN}Documentation built successfully${NC}"
}

# Main script logic
case "$1" in
    deploy)
        check_mike
        deploy_version "$2" "$3"
        ;;
    list)
        check_mike
        list_versions
        ;;
    serve)
        check_mike
        serve_docs
        ;;
    set-default)
        check_mike
        set_default "$2"
        ;;
    delete)
        check_mike
        delete_version "$2"
        ;;
    build)
        build_docs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac