import os

DIR_MD_OUTPUT = os.path.join(os.path.dirname(__file__), "../outputs")
PROMPT_ARCHI = """
## Application General Description
### Description :
The application is a peer-to-peer recommendation system designed for friends. Users can share recommendations about various topics such as restaurants, books, movies, and more. The core functionality revolves around creating, sharing, discovering, and interacting with these recommendations within a social context.

### Architecture 
The application follows an onion (hexagonal) architecture. The backend is built with NodeJS, and the frontend is developed using React as a Progressive Web App (PWA). The API is implemented using GraphQL, and the data is stored in a PostgreSQL database accessed through the Prisma ORM.

## Core Functionalities Overview

### 1. Content Discovery and Feed Management
**Description**: Users can discover recommendations from their friends through a personalized feed. The feed displays posts containing recommendations, including author information, category, title, description, and an image. Users can interact with these posts through actions like liking, commenting, and sharing.
**Related Pages**: Feed screen page, profile-feedscreen page, feed-screen-search page

### 2. User Authentication
**Description**: The application provides a secure authentication mechanism, allowing users to log in using their email and password. A "Forgot password?" feature is also available to assist users in recovering their accounts.
**Related Pages**: Authentification page

### 3. Search and Filtering
**Description**: Users can search for specific recommendations or content within the application. The search functionality is integrated into the feed screen, allowing users to quickly find relevant recommendations based on keywords.
**Related Pages**: Feed screen page, feed-screen-search page

### 4. User Profile and Content Creation
**Description**: Although not explicitly detailed, the presence of user avatars and author information on the feed screen implies the existence of user profiles. Users can likely create and manage their profiles, as well as create and share their own recommendations.
**Related Pages**: Feed screen page, profile-feedscreen page

### 5. Navigation and Notifications
**Description**: A bottom navigation bar provides access to key sections of the application, including the feed, profile, groups/social, history, and notifications. This allows users to easily navigate between different functionalities and stay informed about relevant updates.
**Related Pages**: Feed screen page


"""