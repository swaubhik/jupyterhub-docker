#!/bin/bash

# ============================================================================
# User Management Helper Script
# ============================================================================

set -e

ACTION=$1
USERNAME=$2

show_usage() {
    echo "JupyterHub User Management Script"
    echo ""
    echo "Usage: $0 <command> [username]"
    echo ""
    echo "Commands:"
    echo "  list              - List all users"
    echo "  add <username>    - Add a user to allowed list"
    echo "  remove <username> - Remove a user from allowed list"
    echo "  admin <username>  - Make a user admin"
    echo "  servers           - List active servers"
    echo "  stop <username>   - Stop a user's server"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 add student1"
    echo "  $0 admin instructor"
    echo ""
}

if [ -z "$ACTION" ]; then
    show_usage
    exit 1
fi

case "$ACTION" in
    list)
        echo "Users in users.txt:"
        cat users.txt | grep -v "^#" | grep -v "^$"
        ;;
    
    add)
        if [ -z "$USERNAME" ]; then
            echo "Error: Username required"
            echo "Usage: $0 add <username>"
            exit 1
        fi
        
        if grep -q "^$USERNAME$" users.txt; then
            echo "User '$USERNAME' already exists in users.txt"
        else
            echo "$USERNAME" >> users.txt
            echo "Added user: $USERNAME"
            echo "Restart JupyterHub to apply changes: docker compose restart jupyterhub"
        fi
        ;;
    
    remove)
        if [ -z "$USERNAME" ]; then
            echo "Error: Username required"
            echo "Usage: $0 remove <username>"
            exit 1
        fi
        
        if grep -q "^$USERNAME$" users.txt; then
            # Remove the line (macOS and Linux compatible)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "/^$USERNAME$/d" users.txt
            else
                sed -i "/^$USERNAME$/d" users.txt
            fi
            echo "Removed user: $USERNAME"
            echo "Restart JupyterHub to apply changes: docker compose restart jupyterhub"
        else
            echo "User '$USERNAME' not found in users.txt"
        fi
        ;;
    
    admin)
        if [ -z "$USERNAME" ]; then
            echo "Error: Username required"
            echo "Usage: $0 admin <username>"
            exit 1
        fi
        
        echo "Making '$USERNAME' an admin..."
        echo "Edit jupyterhub_config.py and add '$USERNAME' to:"
        echo "  c.Authenticator.admin_users = {'admin', 'instructor', '$USERNAME'}"
        echo ""
        echo "Then restart: docker compose restart jupyterhub"
        ;;
    
    servers)
        echo "Active JupyterHub servers:"
        docker ps --filter "label=com.jupyterhub.service=notebook" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
        ;;
    
    stop)
        if [ -z "$USERNAME" ]; then
            echo "Error: Username required"
            echo "Usage: $0 stop <username>"
            exit 1
        fi
        
        echo "Stopping server for user: $USERNAME"
        # Find and stop the container for this user
        CONTAINER=$(docker ps --filter "name=jupyter-$USERNAME" --format "{{.Names}}" | head -1)
        
        if [ -z "$CONTAINER" ]; then
            echo "No running server found for user: $USERNAME"
        else
            docker stop "$CONTAINER"
            echo "Stopped server: $CONTAINER"
        fi
        ;;
    
    *)
        echo "Unknown command: $ACTION"
        show_usage
        exit 1
        ;;
esac
