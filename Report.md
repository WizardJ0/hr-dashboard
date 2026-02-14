Business case & objective (2–3 mins)
    Scenario: Recuiters, HR agencies, HR departments usually have no visualisation to help them in their job.
    Only when they gain experience, are they able to do their job better. Not just because of the network they have build, but also of the experience and industry knowledge they have.

    Scenario A: Company A is looking for candidates for 5 roles. 2 roles are paying above their industry salary, while the other 3 roles are paying below industry salary due to budgeting considerations.
    With our dashboard, the HR rep, sales rep is able to have at a glance how the industry is doing, provide high level insights. The rep is able to suggest to Company A, if they are willing to open the role beyond their industry and potentially take canidates from other industry with fitting skillsets to fit their budgeting requirements.

    Scenario B: candidates B has always felt that HR agencies, Recuiters dont understand him well enough, and does not look for his best interest. He is willing to switch industries, has transferrable skills. But does not know the market well enough.
    The HR rep in this instead can efficently and better match the expectations of this candidate, opening the person up for roles beyond his industry


    Users: HR agencies, Recuitment firms, HR Departments 
        
    Objective: Providing a tool to better meet & match expectations of both employers & employees. In line with value Proposition 
        1. Effective matching of candidate profile to job demand and requirement
        2. Better understanding of market trend and competitivenes (To better speak with other HR agencies bring in briefs)
        3. Increase success rate and turnaround time in hiring process (Understanding the candidate & the brief, being informed enough to satisfy both)
    
    Success criteria: Matching expectations of both Employer & Employee


Process & data handling (3–4 mins): How you cleaned, transformed, and explored the data.
- Loads data from a CSV file (SGJobData.csv).
- Drops unnecessary columns.
    expiryDate, PostedOnBehalf, jobPostId, PostingDate, PostingDate, Count, totalNumberOfView, status_id, occupationId
- Removes rows with missing values in critical columns.
    categories, positionLevels, salary_type, title, postedCompany_name
- Filters salary data to a reasonable range.
- Extracts and explodes categories from a JSON-like string.
- Cleans job titles by removing noise like urgency indicators and salary ranges.
- Renames columns for consistency.
- Cleans and converts data types of experience and salary columns.

Dashboard / app walkthrough (3–4 mins): Main views, interactions, and how they answer the business question.
- Side filters: give flexibility in choosing industry, employment types, job status & Average Salary Range
- Market Overview: Quick numbers
- Top Industry by Demand: comparing demand across industries
- Salary vs Experience: Average Salary line chart showing the industry average vs experience
- Available Jobs: Showing the quick view of the job details

Challenges & learnings (1–2 mins): Technical/analytical challenges, what you learned, and possible next steps.
- Cleaning: would like to be more comprehensive, needs alot of real world practise & guidence
- Design: Keeping it simple yet function, remembering it's a tool
- Combining codes from different people
- Limited prompts from AI

