import discord
from discord.ext import commands, tasks
import random
import os
from datetime import datetime, time
import pytz
from dotenv import load_dotenv
import aiohttp
import json
from bs4 import BeautifulSoup
import threading
from flask import Flask, render_template

# Loading environment variables
load_dotenv()

# Configuring intents
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix='!', intents=intents)

# Flask app configuration
app = Flask(__name__, static_folder='static', template_folder='templates')

# Verifying environment variables
try:
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
    if not TOKEN or not CHANNEL_ID:
        raise ValueError("Missing environment variables")
except Exception as e:
    print(f"Configuration error: {e}")
    exit()

# Time configuration
IST = pytz.timezone('Asia/Kolkata')
DAILY_TIME = time(18, 30, tzinfo=IST)  # 6:30 PM IST

# Challenge sources
CHALLENGE_SOURCES = [
    "leetcode",
    "codechef",
    "hackerrank",
    "projecteuler"
]

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')
    print(f'Guilds connected to: {[g.name for g in bot.guilds]}')
    
    # Creating HTTP session for the bot
    bot.session = aiohttp.ClientSession()
    
    try:
        daily_challenge.start()
        print(f'Daily challenge scheduled for {DAILY_TIME} IST')
    except Exception as e:
        print(f"Error starting task: {e}")

@bot.event
async def on_close():
    """Closing the aiohttp session when the bot shuts down"""
    if hasattr(bot, 'session'):
        await bot.session.close()

@tasks.loop(time=DAILY_TIME)
async def daily_challenge():
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            raise ValueError(f"Channel {CHANNEL_ID} not found")
        
        print(f"Sending challenge to channel: {channel.name}")
        
        # Selecting a random source for daily challenge
        source = random.choice(CHALLENGE_SOURCES)
        challenge = await fetch_challenge(source)
        
        await channel.send(embed=challenge)
    except Exception as e:
        print(f"Error in daily challenge: {e}")

async def fetch_challenge(source):
    """Fetching a coding challenge from the specified source"""
    try:
        if source == "leetcode":
            try:
                return await fetch_leetcode_challenge()
            except Exception as e:
                print(f"Primary LeetCode method failed: {e}")
                return await fetch_leetcode_challenge_backup()
        elif source == "codechef":
            return await fetch_codechef_challenge()
        elif source == "hackerrank":
            return await fetch_hackerrank_challenge()
        elif source == "projecteuler":
            return await fetch_projecteuler_challenge()
        else:
            return get_default_challenge()
    except Exception as e:
        print(f"Error fetching challenge from {source}: {e}")
        return get_default_challenge()

async def fetch_leetcode_challenge():
    """Fetching a random LeetCode challenge using GraphQL API"""
    try:
        # Using LeetCode's GraphQL API
        url = "https://leetcode.com/graphql"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }
        
        # Query to get a random list of problems
        query = {
            "query": """
            query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
              problemsetQuestionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
              ) {
                questions {
                  title
                  titleSlug
                  difficulty
                  frontendQuestionId
                }
              }
            }
            """,
            "variables": {
                "categorySlug": "",
                "skip": 0,
                "limit": 50,
                "filters": {}
            }
        }
        
        async with bot.session.post(url, headers=headers, json=query) as response:
            if response.status != 200:
                print(f"LeetCode API returned status {response.status}")
                return await fetch_leetcode_challenge_backup()
                
            try:
                data = await response.json()
                if 'errors' in data:
                    print(f"GraphQL errors: {data['errors']}")
                    return await fetch_leetcode_challenge_backup()
                    
                questions = data['data']['problemsetQuestionList']['questions']
                if not questions:
                    return await fetch_leetcode_challenge_backup()
                    
                # Select a random problem
                problem = random.choice(questions)
                problem_title = problem['title']
                problem_slug = problem['titleSlug']
                difficulty = problem['difficulty']
                problem_id = problem['frontendQuestionId']
                
                # Create problem URL
                problem_url = f"https://leetcode.com/problems/{problem_slug}/"
                
                embed = discord.Embed(
                    title=f"LeetCode Challenge: {problem_title}",
                    description=f"Today's coding challenge from LeetCode!",
                    color=discord.Color.green(),
                    url=problem_url
                )
                
                embed.add_field(name="Problem ID", value=problem_id, inline=True)
                embed.add_field(name="Difficulty", value=difficulty, inline=True)
                embed.add_field(name="Link", value=f"[Solve on LeetCode]({problem_url})", inline=True)
                embed.set_footer(text="Happy coding! 💻")
                
                return embed
            except Exception as json_error:
                print(f"Error parsing LeetCode JSON: {json_error}")
                return await fetch_leetcode_challenge_backup()
    except Exception as e:
        print(f"Error fetching LeetCode challenge: {e}")
        return await fetch_leetcode_challenge_backup()

async def fetch_leetcode_challenge_backup():
    """Fallback method to get LeetCode challenges"""
    try:
        # Getting a random problem from a predefined list
        leetcode_problems = [
            {"id": "1", "title": "Two Sum", "slug": "two-sum", "difficulty": "Easy"},
            {"id": "2", "title": "Add Two Numbers", "slug": "add-two-numbers", "difficulty": "Medium"},
            {"id": "3", "title": "Longest Substring Without Repeating Characters", "slug": "longest-substring-without-repeating-characters", "difficulty": "Medium"},
            {"id": "4", "title": "Median of Two Sorted Arrays", "slug": "median-of-two-sorted-arrays", "difficulty": "Hard"},
            {"id": "5", "title": "Longest Palindromic Substring", "slug": "longest-palindromic-substring", "difficulty": "Medium"},
            {"id": "20", "title": "Valid Parentheses", "slug": "valid-parentheses", "difficulty": "Easy"},
            {"id": "21", "title": "Merge Two Sorted Lists", "slug": "merge-two-sorted-lists", "difficulty": "Easy"},
            {"id": "53", "title": "Maximum Subarray", "slug": "maximum-subarray", "difficulty": "Medium"},
            {"id": "70", "title": "Climbing Stairs", "slug": "climbing-stairs", "difficulty": "Easy"},
            {"id": "121", "title": "Best Time to Buy and Sell Stock", "slug": "best-time-to-buy-and-sell-stock", "difficulty": "Easy"},
            {"id": "200", "title": "Number of Islands", "slug": "number-of-islands", "difficulty": "Medium"},
            {"id": "206", "title": "Reverse Linked List", "slug": "reverse-linked-list", "difficulty": "Easy"},
            {"id": "217", "title": "Contains Duplicate", "slug": "contains-duplicate", "difficulty": "Easy"},
            {"id": "238", "title": "Product of Array Except Self", "slug": "product-of-array-except-self", "difficulty": "Medium"},
            {"id": "242", "title": "Valid Anagram", "slug": "valid-anagram", "difficulty": "Easy"},
            {"id": "322", "title": "Coin Change", "slug": "coin-change", "difficulty": "Medium"},
            {"id": "347", "title": "Top K Frequent Elements", "slug": "top-k-frequent-elements", "difficulty": "Medium"},
            {"id": "424", "title": "Longest Repeating Character Replacement", "slug": "longest-repeating-character-replacement", "difficulty": "Medium"},
            {"id": "647", "title": "Palindromic Substrings", "slug": "palindromic-substrings", "difficulty": "Medium"},
            {"id": "704", "title": "Binary Search", "slug": "binary-search", "difficulty": "Easy"}
        ]
        
        problem = random.choice(leetcode_problems)
        
        problem_url = f"https://leetcode.com/problems/{problem['slug']}/"
        
        embed = discord.Embed(
            title=f"LeetCode Challenge: {problem['title']}",
            description=f"Today's coding challenge from LeetCode!",
            color=discord.Color.green(),
            url=problem_url
        )
        
        embed.add_field(name="Problem ID", value=problem['id'], inline=True)
        embed.add_field(name="Difficulty", value=problem['difficulty'], inline=True)
        embed.add_field(name="Link", value=f"[Solve on LeetCode]({problem_url})", inline=True)
        embed.set_footer(text="Happy coding! 💻")
        
        return embed
    except Exception as e:
        print(f"Error in LeetCode backup method: {e}")
        return get_default_challenge()

async def fetch_codechef_challenge():
    """Fetch a random CodeChef challenge"""
    try:
        # Get a list of practice problems
        url = "https://www.codechef.com/api/list/problems?categorySlug=practice&limit=20&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with bot.session.get(url, headers=headers) as response:
            data = await response.json()
            
            if not data or "problemsList" not in data:
                return get_default_challenge()
                
            # Select a random problem
            problem = random.choice(data["problemsList"])
            problem_code = problem["problemCode"]
            problem_name = problem["problemName"]
            difficulty = problem.get("difficulty", "Unknown")
            
            # Create problem URL
            problem_url = f"https://www.codechef.com/problems/{problem_code}"
            
            embed = discord.Embed(
                title=f"CodeChef Challenge: {problem_name}",
                description=f"Today's coding challenge from CodeChef!",
                color=discord.Color.orange(),
                url=problem_url
            )
            
            embed.add_field(name="Problem Code", value=problem_code, inline=True)
            embed.add_field(name="Difficulty", value=difficulty, inline=True)
            embed.add_field(name="Link", value=f"[Solve on CodeChef]({problem_url})", inline=False)
            embed.set_footer(text="Happy coding! 💻")
            
            return embed
    except Exception as e:
        print(f"Error fetching CodeChef challenge: {e}")
        return get_default_challenge()

async def fetch_hackerrank_challenge():
    """Fetch a random HackerRank challenge"""
    # This is a simplified implementation since HackerRank doesn't have a public API
    # We'll pick from a list of common categories and provide a search link
    
    categories = [
        "algorithms", "data-structures", "mathematics", "python", "sql",
        "functional-programming", "ai", "databases", "regex", "security"
    ]
    
    selected_category = random.choice(categories)
    search_url = f"https://www.hackerrank.com/domains/{selected_category}"
    
    embed = discord.Embed(
        title=f"HackerRank: {selected_category.replace('-', ' ').title()} Challenges",
        description=f"Today's challenge category from HackerRank!",
        color=discord.Color.dark_green(),
        url=search_url
    )
    
    embed.add_field(name="Category", value=selected_category.replace('-', ' ').title(), inline=True)
    embed.add_field(name="Link", value=f"[Browse Challenges]({search_url})", inline=True)
    embed.set_footer(text="Choose a challenge that interests you and start coding! 💻")
    
    return embed

async def fetch_projecteuler_challenge():
    """Fetch a random Project Euler challenge"""
    try:
        # Project Euler has over 800 problems, we'll randomly select one
        problem_id = random.randint(1, 150)  # Limiting to the first 150 problems which are more accessible
        problem_url = f"https://projecteuler.net/problem={problem_id}"
        
        # Scrape the problem title
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with bot.session.get(problem_url, headers=headers) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            title_element = soup.find('h2')
            problem_title = f"Problem {problem_id}"
            if title_element:
                problem_title = title_element.text.strip()
            
            embed = discord.Embed(
                title=f"Project Euler: {problem_title}",
                description=f"Today's mathematical programming challenge from Project Euler!",
                color=discord.Color.purple(),
                url=problem_url
            )
            
            embed.add_field(name="Problem ID", value=str(problem_id), inline=True)
            embed.add_field(name="Link", value=f"[View Problem]({problem_url})", inline=True)
            embed.set_footer(text="Project Euler problems combine mathematics and programming! 🧮💻")
            
            return embed
    except Exception as e:
        print(f"Error fetching Project Euler challenge: {e}")
        return get_default_challenge()

def get_default_challenge():
    """Default challenge when API fetching fails"""
    coding_problems = [
        {
            "title": "Two Sum",
            "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            "difficulty": "Easy"
        },
        {
            "title": "Palindrome Check",
            "description": "Write a function that checks if a given string is a palindrome.",
            "difficulty": "Easy"
        },
        {
            "title": "FizzBuzz",
            "description": "Print numbers from 1 to n. For multiples of 3, print 'Fizz'. For multiples of 5, print 'Buzz'. For multiples of both, print 'FizzBuzz'.",
            "difficulty": "Easy"
        },
        {
            "title": "Balanced Brackets",
            "description": "Write a function that determines if a string of brackets is balanced.",
            "difficulty": "Medium"
        },
        {
            "title": "Merge Intervals",
            "description": "Given a collection of intervals, merge all overlapping intervals.",
            "difficulty": "Medium"
        }
    ]
    
    problem = random.choice(coding_problems)
    
    embed = discord.Embed(
        title=f"Daily Coding Challenge: {problem['title']}",
        description=problem['description'],
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Difficulty", value=problem['difficulty'], inline=True)
    embed.set_footer(text="API fetch failed, so here's a classic problem to solve! 💻")
    
    return embed

@bot.command()
async def challenge(ctx, source=None):
    """Command to get a coding challenge on demand"""
    try:
        if source and source.lower() in CHALLENGE_SOURCES:
            challenge_embed = await fetch_challenge(source.lower())
            await ctx.send(f"Here's a challenge from {source}:", embed=challenge_embed)
        else:
            # If no source specified or invalid source, send a random challenge
            source = random.choice(CHALLENGE_SOURCES)
            challenge_embed = await fetch_challenge(source)
            await ctx.send(f"Here's a random challenge from {source}:", embed=challenge_embed)
    except Exception as e:
        print(f"Challenge command error: {e}")
        await ctx.send("Error fetching challenge. Please try again later.")

@bot.command()
async def sources(ctx):
    """List all available challenge sources"""
    sources_list = ", ".join([f"`{source}`" for source in CHALLENGE_SOURCES])
    await ctx.send(f"Available challenge sources: {sources_list}\n\nUse `!challenge <source>` to get a specific challenge!")

@bot.command()
async def help_coder(ctx):
    """Show help information for bot commands"""
    embed = discord.Embed(
        title="Daily Coder Bot - Help",
        description="This bot provides daily coding challenges to keep your skills sharp!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Commands",
        value=(
            "`!challenge` - Get a random coding challenge\n"
            "`!challenge <source>` - Get a challenge from a specific source\n"
            "`!sources` - List all available challenge sources\n"
            "`!test` - Check if the bot is responding\n"
            "`!help_coder` - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Daily Challenge",
        value=f"A random challenge is posted automatically at {DAILY_TIME.strftime('%H:%M')} IST every day!",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def test(ctx):
    """Test command to verify basic functionality"""
    try:
        await ctx.send("Bot is responding! ✅")
        print(f"Test command received from {ctx.author}")
    except Exception as e:
        print(f"Test command error: {e}")

def run_bot():
    """Function to run the Discord bot"""
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Invalid bot token. Please check your .env file")
    except Exception as e:
        print(f"Unexpected error: {e}")

def run_flask():
    """Function to run the Flask app"""
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    print("Starting services...")
    
    # Start Discord bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask app in the main thread
    run_flask()