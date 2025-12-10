# UniVerse - Alumni & Student Networking Platform

**UniVerse** is a comprehensive web application designed to connect students and alumni, fostering a vibrant community for knowledge sharing, career development, and networking. It provides features like user profiles, connection management, real-time chat, an expert Q&A forum, event listings (hackathons, career fairs, jobs, internships), leaderboards, a daily engagement prompt (Daily Spark), alumni career roadmaps, and a robust admin panel for site management.

## ✨ Features

**Core User Experience (Students & Alumni):**

*   **Authentication:** Secure user registration (with distinct roles: Student, Alumni, Admin), login, logout.
*   **Personalized Dashboard/Home:** A central landing page after login, potentially displaying a personalized feed of relevant activities, upcoming events, new Q&A, or Daily Spark prompts.
*   **User Profiles:**
    *   Viewable public profiles displaying professional information (profession, current company, department, alma mater).
    *   Sections for users to share interview experiences, internship experiences, startup ventures, personal milestones, and career advice.
    *   Display of user engagement metrics: activity score, **Alumni Gems**, badge count, solved challenges, and number of connections.
    *   Logged-in users can edit their own profiles.
*   **Networking & Connections (My Network):**
    *   Search for other users by name, profession, department, etc.
    *   Send, accept, and ignore connection requests.
    *   View a list of established connections with options to message or remove.
    *   Receive suggestions for "People You May Know."
*   **Real-Time Chat:**
    *   One-on-one private messaging with established connections.
    *   Sidebar listing active conversations and contacts.
    *   Ability to initiate chats from user profiles or the network page by clicking on a connection.
    *   (Conceptual) File sharing within chats.
*   **Notifications:** (Backend support is present)
    *   Alerts for new connection requests, accepted requests, new messages (if chat notifications are added), event updates, and other relevant activities. *Frontend display of notifications is a key area for future development.*

**Knowledge Sharing, Engagement & Opportunities:**

*   **Expert Q&A:**
    *   All users can submit questions to the community.
    *   **Alumni-Specific Feature:** After a designated time daily (e.g., 8 PM), a selection of top-liked or recent questions are highlighted for **Alumni** to provide expert answers, leveraging their experience.
    *   Users can like questions and answers.
    *   Dedicated views for "Your Questions" and "Popular Community Questions."
*   **Daily Spark:**
    *   A daily thought-provoking question or prompt presented to all users.
    *   Users can submit their answers/thoughts.
    *   Users can vote (upvote/downvote) on others' answers to the Daily Spark.
*   **Alumni Roadmaps:**
    *   A dedicated section where alumni can share their career journeys, outline steps taken, offer advice, and provide insights into their career paths. This helps students and other alumni learn from real-world experiences.
*   **Opportunity Submissions & Browsing (Admin Verified):**
    *   Users (especially alumni) can suggest new listings for:
        *   **Hackathons:** Discover and submit hackathon details.
        *   **Career Fairs:** Find and suggest career fair information.
        *   **Job Listings:** Submit job opportunities.
        *   **Internships:** Suggest internship openings.
    *   All submissions are reviewed and verified by an Admin before being published.
    *   Users can browse approved and active opportunities.
*   **Explore Page:** A central hub for users to discover various opportunities (Jobs, Internships, Hackathons, Career Fairs) and potentially other community content.

**Recognition & Gamification:**

*   **Leaderboard:**
    *   Showcases top **Alumni** contributors based on "Alumni Gems" and activity.
    *   Sortable by different criteria (Gems, Name).
    *   Clickable entries leading to user profiles.
*   **Alumni Gems:** A points system specifically for alumni, awarded for valuable contributions such as:
    *   Answering questions in the Expert Q&A.
    *   Submitting verifiable opportunities (jobs, internships, hackathons, career fairs).
    *   Asking insightful questions.
    *   Engaging with content (e.g., liking questions, upvoting Daily Spark answers).
*   **Last Active Tracking:** User activity is tracked via a `last_active` timestamp, which can be used for features like identifying inactive users.

**Administrative Capabilities (Admin Panel):**

*   **Admin Dashboard:** Central overview and access to management tools.
*   **User Management:**
    *   Comprehensive list of all users with search and filtering (including active, deactivated, and inactive candidates).
    *   View detailed user profiles.
    *   Approve user roles (Student, Alumni) for new sign-ups or role changes.
    *   Grant or revoke Administrator privileges.
    *   Activate or deactivate user accounts (soft delete).
    *   Specific view for "Inactive User Candidates" (active users not seen for >90 days) to prompt admin review and potential deactivation.
    *   (Requires Backend Endpoint) Option to permanently delete user accounts (with strong confirmations).
*   **Event & Submission Management:** (Admin interface needed for full functionality)
    *   System for admins to review, approve, edit, or reject user-submitted content:
        *   Hackathons
        *   Career Fairs
        *   Job Listings
        *   Internships
    *   Manage existing event listings (e.g., edit details, mark as expired).
    *   Potentially manage Daily Spark questions (e.g., add new ones, archive old ones).
*   **Feedback Management:** (Admin interface needed)
    *   A system to view, categorize, and act upon user-submitted feedback or reports regarding content or users.

---
