# AI Job Search Agent

A production-grade job search agent that aggregates jobs from 20+ sources, ranks them using AI, and provides comprehensive career intelligence based on your professional identity.

## Features

- **Multi-Source Aggregation**: Scrapes jobs from 20+ remote job boards and platforms
- **AI-Powered Ranking**: Uses LLM to rank jobs based on your professional identity and skills
- **Career Intelligence**: Provides opportunity scores, skill gap analysis, and career trajectory predictions
- **Professional Identity Matching**: Matches jobs to your primary/secondary skills and target roles
- **Worldwide Remote Support**: Optimized for global remote job searches
- **Real-time Filtering**: Filter by location, salary, seniority, work type, and posting date

## Supported Job Sources

| Source | Type |
|--------|------|
| LinkedIn | Professional Network |
| RemoteOK | Remote Jobs |
| WeWorkRemotely | Remote Jobs |
| WorkingNomads | Nomad Jobs |
| Himalayas | Remote Jobs |
| RemoteHub | Remote Jobs |
| RemoteRocketship | Remote Jobs |
| TrulyRemote | Remote Jobs |
| Remotive | Remote Jobs |
| Jobicy | Remote Jobs |
| Arbeitnow | Global Jobs |
| BuiltIn | Tech Jobs |
| Levels.fyi | Tech Salaries |
| Jooble | Job Aggregator |
| Hubstaff Talent | Remote Jobs |
| HiringCafe | Remote Jobs |
| Reed | UK Jobs |
| Remote.io | Remote Jobs |
| CryptoJobsList | Crypto/Web3 |
| NodeSk | Remote Jobs |
| Workway | Remote Jobs |

## Tech Stack

- **Orchestration**: LangGraph `StateGraph` for workflow management
- **AI/LLM**: Groq API (Llama 3.3 70B) for query parsing and job ranking
- **Scraping**: BeautifulSoup4 for HTML parsing
- **Database**: SQLite with LangGraph checkpointing
- **Frontend**: Streamlit for interactive UI
- **HTTP**: Requests library for API calls

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd job-ai-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
JOB_PLATFORM_API_KEY="your_groq_api_key"
```

4. Run the application:
```bash
streamlit run app/streamlit_app.py
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JOB_PLATFORM_API_KEY` | Groq API key for LLM services | Yes |
| `JOOBLE_API_KEY` | Jooble API key (optional) | No |

### User Profile

Configure your professional identity in the sidebar:

- **Professional Headline**: e.g., "Senior Java Backend Engineer"
- **Primary Skills**: Core skills for matching (comma-separated)
- **Secondary Skills**: Complementary skills
- **Target Roles**: Job titles you're targeting
- **Rejection Rules**: Languages, frameworks, or roles to exclude

## Usage

### Search Queries

Use natural language queries to search for jobs:

```
Senior java developer remote in Tbilisi
Python engineer salary 5000 usd
React developer remote worldwide posted today
AI engineer remote worldwide
Junior developer in Batumi last 7 days
```

### Query Format

```
[seniority] [role] [work_type] in [location] salary [amount] posted [when]
```

| Component | Options |
|-----------|---------|
| Seniority | `senior`, `junior`, `intern`, `lead`, `staff`, `principal` |
| Work Type | `remote`, `hybrid`, `office`, `worldwide` |
| Posted | `today`, `this week`, `this month`, `last N days` |

## Project Structure

```
job-ai-agent/
├── app/
│   ├── agent/           # AI agents and ranking logic
│   │   ├── ranker.py           # Job ranking with LLM
│   │   ├── career_match.py     # Opportunity scoring
│   │   ├── career_intelligence.py # Intelligence reports
│   │   ├── professional_identity.py # Identity matching
│   │   └── skill_roi.py        # Skill learning ROI
│   ├── crawlers/        # Job source scrapers
│   │   ├── manager.py          # Crawler orchestration
│   │   ├── remoteok.py         # RemoteOK scraper
│   │   ├── linkedin.py         # LinkedIn scraper
│   │   └── ...                 # 20+ other crawlers
│   ├── graph/           # LangGraph workflow
│   │   ├── workflow.py         # Main workflow definition
│   │   ├── state.py            # State management
│   │   └── nodes/              # Workflow nodes
│   │       ├── understand_query.py  # Query parsing
│   │       ├── scrape_jobs.py       # Job scraping
│   │       ├── filter_jobs.py       # Job filtering
│   │       └── rank_jobs.py         # Job ranking
│   ├── db/              # Database layer
│   │   ├── sqlite.py           # SQLite operations
│   │   └── repository.py      # Data repository
│   ├── auth/            # Authentication
│   ├── utils/           # Utilities
│   └── streamlit_app.py # Main application
├── config.json          # Configuration
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Features in Detail

### 1. Query Parsing

The system uses both regex and LLM to parse search queries:
- Extracts keywords, seniority, location, work type, salary, and posting date
- Supports natural language queries
- Handles worldwide/remote job searches

### 2. Job Filtering

Multi-stage filtering ensures relevant results:
- **Role Compatibility**: Matches job titles to your profession
- **Location Matching**: Supports worldwide, remote, and specific locations
- **Work Type**: Filters by remote, hybrid, or office
- **Seniority**: Matches experience levels
- **Salary**: Filters by salary range
- **Posting Date**: Filters by recency

### 3. AI Ranking

Jobs are ranked using:
- **Identity Alignment**: How well the job matches your professional identity
- **Skill Match**: Primary and secondary skill matching
- **Opportunity Score**: Technical fit, salary, career growth, hiring probability
- **Query Relevance**: Match to search query keywords

### 4. Career Intelligence

Comprehensive reports include:
- **Current Employability**: Your readiness level based on identity alignment
- **Opportunity Scores**: Detailed scoring for each job
- **Skill Gap Analysis**: Skills to learn with ROI calculations
- **Career Trajectory**: Predicted career direction

## API Integration

### Groq API

Used for:
- Query parsing and understanding
- Job ranking and scoring
- Career intelligence generation

### Job Board APIs

Some crawlers require API keys:
- **Jooble**: Set `JOOBLE_API_KEY` in `.env`
- **LinkedIn**: Requires browser cookies for authentication

## Development

### Adding New Crawlers

1. Create a new file in `app/crawlers/`
2. Implement the `crawl(keywords, location)` method
3. Return list of job dicts with: `title`, `company`, `url`, `location`, `description`, `source`
4. Add the crawler to `app/crawlers/manager.py`

### Customizing Ranking

Edit `app/agent/ranker.py` to adjust:
- Scoring weights
- Identity alignment thresholds
- Skill matching logic

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
