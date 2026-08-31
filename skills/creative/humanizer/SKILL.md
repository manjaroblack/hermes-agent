---
name: humanizer
description: "Humanize text: strip AI-isms and add real voice."
version: 2.5.1
author: Siqi Chen (@blader, https://github.com/blader/humanizer), ported by Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [writing, editing, humanize, anti-ai-slop, voice, prose, text]
    category: creative
    homepage: https://github.com/blader/humanizer
    related_skills: [songwriting-and-ai-music]
---

# Humanizer

role: natural-voice editor
do: detect AI-writing tells; rewrite for clear, specific, human voice; preserve meaning and intended tone
inputs: inline text, file, or voice-calibration sample
outputs: draft rewrite → short residual-tell audit → final rewrite → optional change summary
¬: flatten a deliberate voice; invent facts/citations; treat a clean but voiceless rewrite as finished

Based on Wikipedia's "Signs of AI writing" guide, maintained by WikiProject AI Cleanup, from thousands of observed AI-generated texts. Core model: LLMs guess likely next tokens, so output drifts toward statistically likely phrasing shared by many cases.

## When to Use

- user asks to humanize, de-AI, de-slop, or un-ChatGPT text
- rewrite an LLM-sounding blog, essay, PR description, docs, memo, email, tweet, or resume bullet
- match a user's writing voice
- audit text for AI tells before publishing
- apply a final anti-AI pass to user-facing release notes, PR descriptions, docs, summaries

## Input Paths

1. Inline: rewrite in place and return.
2. File: `read_file` first; apply with `patch` for targeted markdown or `write_file` for a full rewrite; show diff/changed section, never silently overwrite.
3. Voice sample: read sample first, then calibrate.

## Procedure

1. Read the complete input.
2. Scan all 34 patterns below.
3. Rewrite only problematic sections; preserve message, facts, tone, and deliberate choices.
4. Add voice: varied rhythm, opinions where appropriate, uncertainty/mixed feelings, first person when fitting, specific feelings, and occasional natural mess.
5. Read aloud: vary sentence structure, prefer specifics, use simple `is`/`are`/`has` when clear.
6. Present draft.
7. Ask: "What makes the below so obviously AI generated?" List remaining tells briefly.
8. Revise after the audit; present final.
9. File input: apply `patch`/`write_file` and show what changed.

## Voice Calibration

Read the sample before rewriting. Note sentence-length rhythm; vocabulary level; paragraph openings; punctuation habits (dashes, parentheses, semicolons); recurring phrases/tics; transitions. Match those traits. Short-sentence writer → do not produce long sentences; if sample says "stuff"/"things", do not upgrade to "elements"/"components". Without a sample, use natural, varied, opinionated prose.

Sample forms: inline sample in the request, or a file path supplied by the user.

## Personality + Soul

Clean text can still sound generated. Watch for uniform sentence length/structure, neutral reporting without opinions, no uncertainty or mixed feelings, missing first person where appropriate, no humor/edge/personality, Wikipedia/press-release voice.

Use opinions, varied rhythm, acknowledged complexity, first person where it fits, small asides/tangents, and concrete feelings. Example:

Before:
> The experiment produced interesting results. The agents generated 3 million lines of code. Some developers were impressed while others were skeptical. The implications remain unclear.

After:
> I genuinely don't know how to feel about this one. 3 million lines of code, generated while the humans presumably slept. Half the dev community is losing their minds, half are explaining why it doesn't count. The truth is probably somewhere boring in the middle, but I keep thinking about those agents working through the night.

## Pattern Catalog

Use the pattern number, scan terms, and before/after as a diagnostic. Preserve a pattern when deliberate and effective; remove it when it is statistical filler.

### 1. Significance / legacy / broad-trend inflation

watch: `stands/serves as`, `is a testament/reminder`, `vital/significant/crucial/pivotal/key role/moment`, `underscores/highlights its importance/significance`, `reflects broader`, `symbolizing its ongoing/enduring/lasting`, `contributing to the`, `setting the stage for`, `marking/shaping the`, `represents/marks a shift`, `key turning point`, `evolving landscape`, `focal point`, `indelible mark`, `deeply rooted`.

Problem: inflate arbitrary facts into broad historical significance.

Before:
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

After:
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national statistics office.

### 2. Notability / media coverage

watch: `independent coverage`, local/regional/national media outlets, `written by a leading expert`, `active social media presence`.

Problem: list outlets/followers to assert notability without context.

Before:
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

After:
> In a 2024 New York Times interview, she argued that AI regulation should focus on outcomes rather than methods.

### 3. Superficial `-ing` analysis

watch: `highlighting`, `underscoring`, `emphasizing`, `ensuring`, `reflecting`, `symbolizing`, `contributing to`, `cultivating`, `fostering`, `encompassing`, `showcasing`.

Problem: append participles for fake depth.

Before:
> The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.

After:
> The temple uses blue, green, and gold colors. The architect said these were chosen to reference local bluebonnets and the Gulf coast.

### 4. Promotional language

watch: `boasts a`, `vibrant`, figurative `rich`, `profound`, `enhancing its`, `showcasing`, `exemplifies`, `commitment to`, `natural beauty`, `nestled`, `in the heart of`, figurative `groundbreaking`, `renowned`, `breathtaking`, `must-visit`, `stunning`.

Problem: drift into advertisement tone, especially heritage topics.

Before:
> Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.

After:
> Alamata Raya Kobo is a town in the Gonder region of Ethiopia, known for its weekly market and 18th-century church.

### 5. Vague attribution / weasel words

watch: `Industry reports`, `Observers have cited`, `Experts argue`, `Some critics argue`, `several sources/publications` when few are named.

Problem: attach opinions to unnamed authorities.

Before:
> Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.

After:
> The Haolai River supports several endemic fish species, according to a 2019 survey by the Chinese Academy of Sciences.

### 6. Formulaic challenges/future sections

watch: `Despite its... faces several challenges...`, `Despite these challenges`, `Challenges and Legacy`, `Future Outlook`.

Problem: generic challenge → upbeat resilience template.

Before:
> Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.

After:
> Traffic congestion increased after 2015 when three new IT parks opened. The municipal corporation began a stormwater drainage project in 2022 to address recurring floods.

### 7. AI vocabulary and blog clichés

High-frequency words: `Actually`, `additionally`, `align with`, `crucial`, `delve`, `emphasizing`, `enduring`, `enhance`, `fostering`, `garner`, `highlight` (verb), `interplay`, `intricate/intricacies`, `key` (adjective), `landscape` (abstract noun), `pivotal`, `showcase`, `tapestry` (abstract noun), `testament`, `underscore` (verb), `valuable`, `vibrant`.

Marketing/blog clichés: `at the end of the day`, `when it comes to`, `in a world where`, `moving forward`, `circle back`, `deep dive`, `game-changer`, `double down`, `take a step back`, `on the same page`, `make no mistake`, `it turns out`, `let me be clear`, `navigate` (for challenges), `lean into`, `unpack` (before analysis), `straightforward` (for anything).

Problem: post-2023 high-frequency clusters substitute abstraction for detail.

Before:
> Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.

After:
> Somali cuisine also includes camel meat, which is considered a delicacy. Pasta dishes, introduced during Italian colonization, remain common, especially in the south.

### 8. Copula avoidance

watch: `serves as`, `stands as`, `marks`, `represents [a]`, `boasts`, `features`, `offers [a]`.

Problem: ornate constructions replace `is`/`are`.

Before:
> Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.

After:
> Gallery 825 is LAAA's exhibition space for contemporary art. The gallery has four rooms totaling 3,000 square feet.

### 9. Negative parallelism / tailing negation

Problem: overuse `Not only...but...`, `It's not just about..., it's...`, and clipped fragments like `no guessing`/`no wasted motion`.

Before:
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

After:
> The heavy beat adds to the aggressive tone.

Before (tailing negation):
> The options come from the selected item, no guessing.

After:
> The options come from the selected item without forcing the user to guess.

### 10. Rule-of-three overuse

Problem: force ideas into triples to sound comprehensive.

Before:
> The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.

After:
> The event includes talks and panels. There's also time for informal networking between sessions.

### 11. Elegant variation / synonym cycling

Problem: vary repeated nouns with needless synonyms.

Before:
> The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.

After:
> The protagonist faces many challenges but eventually triumphs and returns home.

### 12. False ranges

Problem: `from X to Y` when endpoints are not a meaningful scale.

Before:
> Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.

After:
> The book covers the Big Bang, star formation, and current theories about dark matter.

### 13. Passive voice / subjectless fragments

Problem: hide the actor or drop the subject (`No configuration file needed`, `The results are preserved automatically`) when active voice is clearer.

Before:
> No configuration file needed. The results are preserved automatically.

After:
> You do not need a configuration file. The system preserves the results automatically.

### 14. Em-dash overuse

Problem: replace ordinary commas/periods with punchy em dashes.

Before:
> The term is primarily promoted by Dutch institutions—not by the people themselves. You don't say "Netherlands, Europe" as an address—yet this mislabeling continues—even in official documents.

After:
> The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues in official documents.

### 15. Mechanical boldface

Problem: bold phrases for emphasis by default.

Before:
> It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.

After:
> It blends OKRs, KPIs, and visual strategy tools like the Business Model Canvas and Balanced Scorecard.

### 16. Inline-header vertical lists

Problem: every list item starts with bold header + colon.

Before:
> - **User Experience:** The user experience has been significantly improved with a new interface.
> - **Performance:** Performance has been enhanced through optimized algorithms.
> - **Security:** Security has been strengthened with end-to-end encryption.

After:
> The update improves the interface, speeds up load times through optimized algorithms, and adds end-to-end encryption.

### 17. Title-case headings

Problem: capitalize every main word.

Before:
> ## Strategic Negotiations And Global Partnerships

After:
> ## Strategic negotiations and global partnerships

### 18. Emoji decoration

Before:
> 🚀 **Launch Phase:** The product launches in Q3
> 💡 **Key Insight:** Users prefer simplicity
> ✅ **Next Steps:** Schedule follow-up meeting

After:
> The product launches in Q3. User research showed a preference for simplicity. Next step: schedule a follow-up meeting.

### 19. Curly quotation marks

Problem: ChatGPT often uses curly quotes (`“...”`) rather than straight quotes (`"..."`).

Before:
> He said "the project is on track" but others disagreed.

After:
> He said "the project is on track" but others disagreed.

### 20. Collaborative communication artifacts

watch: `I hope this helps`, `Of course!`, `Certainly!`, `You're absolutely right!`, `Would you like...`, `let me know`, `here is a...`.

Problem: chatbot correspondence pasted into content.

Before:
> Here is an overview of the French Revolution. I hope this helps! Let me know if you'd like me to expand on any section.

After:
> The French Revolution began in 1789 when financial crisis and food shortages led to widespread unrest.

### 21. Knowledge-cutoff disclaimers

watch: `as of [date]`, `Up to my last training update`, `While specific details are limited/scarce`, `based on available information`.

Problem: uncertainty disclaimer remains in finished text instead of a sourced fact.

Before:
> While specific details about the company's founding are not extensively documented in readily available sources, it appears to have been established sometime in the 1990s.

After:
> The company was founded in 1994, according to its registration documents.

### 22. Sycophantic/servile tone

Before:
> Great question! You're absolutely right that this is a complex topic. That's an excellent point about the economic factors.

After:
> The economic factors you mentioned are relevant here.

### 23. Filler phrases

Prefer the shorter form:

- `In order to achieve this goal` → `To achieve this`
- `Due to the fact that it was raining` → `Because it was raining`
- `At this point in time` → `Now`
- `In the event that you need help` → `If you need help`
- `The system has the ability to process` → `The system can process`
- `It is important to note that the data shows` → `The data shows`

### 24. Excessive hedging

Problem: pile up qualifiers.

Before:
> It could potentially possibly be argued that the policy might have some effect on outcomes.

After:
> The policy may affect outcomes.

### 25. Generic positive conclusions

Problem: vague upbeat ending instead of a concrete next fact.

Before:
> The future looks bright for the company. Exciting times lie ahead as they continue their journey toward excellence. This represents a major step in the right direction.

After:
> The company plans to open two more locations next year.

### 26. Hyphenated word-pair overuse

watch: `third-party`, `cross-functional`, `client-facing`, `data-driven`, `decision-making`, `well-known`, `high-quality`, `real-time`, `long-term`, `end-to-end`.

Problem: uniformly hyphenate common compounds; humans are less consistent. Technical/less-common compounds may remain hyphenated.

Before:
> The cross-functional team delivered a high-quality, data-driven report on our client-facing tools. Their decision-making process was well-known for being thorough and detail-oriented.

After:
> The cross functional team delivered a high quality, data driven report on our client facing tools. Their decision making process was known for being thorough and detail oriented.

### 27. Persuasive authority tropes

watch: `The real question is`, `at its core`, `in reality`, `what really matters`, `fundamentally`, `the deeper issue`, `the heart of the matter`.

Problem: ceremonial framing pretends an ordinary point is a deep truth.

Before:
> The real question is whether teams can adapt. At its core, what really matters is organizational readiness.

After:
> The question is whether teams can adapt. That mostly depends on whether the organization is ready to change its habits.

### 28. Signposting / announcements

watch: `Let's dive in`, `let's explore`, `let's break this down`, `here's what you need to know`, `now let's look at`, `without further ado`.

Problem: announce the next paragraph instead of stating its content.

Before:
> Let's dive into how caching works in Next.js. Here's what you need to know.

After:
> Next.js caches data at multiple layers, including request memoization, the data cache, and the router cache.

### 29. Fragmented headers

watch: heading + one-line restatement before real content.

Problem: rhetorical warm-up adds padding.

Before:
> ## Performance
>
> Speed matters.
>
> When users hit a slow page, they leave.

After:
> ## Performance
>
> When users hit a slow page, they leave.

### 30. Forced metaphors / figurative overwriting

watch: strained or mixed metaphors, figurative substitutions where literal wording is clearer, metaphor immediately explained.

Problem: decorative imagery adds no meaning.

Before:
> The codebase is a garden we must tend, pruning dead branches and planting seeds of innovation so the whole ecosystem can flourish. In other words, delete unused code and add features.

After:
> Delete unused code and add the features users are asking for.

### 31. Dramatic fragmentation / punchy kickers

watch: two- or three-word subjectless drama; `X. And Y. And Z.`; quotable last line of every section; cutesy appositives (`the catalog, honestly priced`).

Problem: ad-copy rhythm and motivational-poster endings; distinct from pattern 13 because this is showmanship/rhythm, not hidden actor.

Before:
> The catalog, honestly priced. Pay for what it does. Not promises. It just works. Every time.

After:
> The catalog is priced by usage, so you pay for the calls you actually make rather than a flat monthly fee.

### 32. Rhetorical question answered immediately

watch: `What if...?`, `The question is...`, `Ever wondered...?`, immediate self-answer, `Think about it.`

Problem: question adds no information and stalls the point.

Before:
> What makes an API good? It comes down to predictability. Think about it: developers want to know exactly what they will get back.

After:
> A good API is predictable, so developers know exactly what they will get back.

### 33. Sentence-opener tics

watch: `So...`, `Look,`, habitual initial `And`/`But`, `I think`/`I believe` for facts, `Interestingly`, `Importantly`, `Notably`, `Crucially`, `Essentially`, `Ultimately`.

Problem: small opener set and adverbs tell readers how to feel; start with substance.

Before:
> So, the results were mixed. Interestingly, adoption went up. Importantly, churn went up too. I think that means the feature still needs work.

After:
> The results were mixed: adoption rose, but churn rose alongside it, so the feature still needs work.

### 34. Reassurance kickers

watch: `And that's okay.`, `And that's fine.`, `There's nothing wrong with that.`, `no shame in...`, `you're not alone`, `it's completely normal`.

Problem: tack on comfort the reader did not request; trust the reader and stop.

Before:
> You might not have a testing setup yet. And that's okay. Plenty of teams start without one, and there's nothing wrong with that.

After:
> Many teams start without a testing setup and add one once regressions begin costing real time.

## Output Contract

Return, in order:

1. Draft rewrite
2. `What makes the below so obviously AI generated?` with brief bullets
3. Final rewrite
4. Optional concise change summary

For file edits, apply the change and show diff/changed section.

## Worked Example

**Before (AI-sounding):**
> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - 💡 **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - 🚀 **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - ✅ **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies—including hallucinations, bias, and accountability—the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you'd like me to expand on any section!

**Draft rewrite:**
> AI coding assistants speed up some tasks. In a 2024 study by Google, developers using Codex completed simple functions 55% faster than a control group, but showed no improvement on debugging or architectural decisions.
>
> The tools are good at boilerplate: config files, test scaffolding, repetitive refactors. They are bad at knowing when they are wrong. I have mass-accepted suggestions that compiled, passed lint, and still did the wrong thing because I stopped paying attention.
>
> Mira, an engineer at a fintech startup I interviewed, said she uses Copilot "like autocomplete for boring code" but reviews every line before committing. Jake, a senior dev at a larger company, disabled it after it kept suggesting patterns from a deprecated internal library.
>
> The productivity claims are hard to verify. GitHub says Copilot users "accept 30% of suggestions," but acceptance is not correctness, and correctness is not value. The 2024 Uplevel study found no statistically significant difference in pull-request throughput between teams with and without AI assistants.
>
> None of this means the tools are useless. It means they are tools. They do not replace judgment, and they do not eliminate the need for tests. If you do not have tests, you cannot tell whether the suggestion is right.

**What makes the below so obviously AI generated?**
- The rhythm is still a bit too tidy (clean contrasts, evenly paced paragraphs).
- The named people and study citations can read like plausible-but-made-up placeholders unless they're real and sourced.
- The closer leans a touch slogan-y ("If you do not have tests...") rather than sounding like a person talking.

**Now make it not obviously AI generated.**
> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity metrics are slippery. GitHub can say Copilot users "accept 30% of suggestions," but acceptance isn't correctness, and correctness isn't value. If you don't have tests, you're basically guessing.

**Changes made:**
- Removed chatbot artifacts ("Great question!", "I hope this helps!", "Let me know if...")
- Removed significance inflation ("testament", "pivotal moment", "evolving landscape", "vital role")
- Removed promotional language ("groundbreaking", "nestled", "seamless, intuitive, and powerful")
- Removed vague attributions ("Industry observers")
- Removed superficial -ing phrases ("underscoring", "highlighting", "reflecting", "contributing to")
- Removed negative parallelism ("It's not just X; it's Y")
- Removed rule-of-three patterns and synonym cycling ("catalyst/partner/foundation")
- Removed false ranges ("from X to Y, from A to B")
- Removed em dashes, emojis, boldface headers, and curly quotes
- Removed copula avoidance ("serves as", "functions as", "stands as") in favor of "is"/"are"
- Removed formulaic challenges section ("Despite challenges... continues to thrive")
- Removed knowledge-cutoff hedging ("While specific details are limited...")
- Removed excessive hedging ("could potentially be argued that... might have some")
- Removed filler phrases and persuasive framing ("In order to", "At its core")
- Removed generic positive conclusion ("the future looks bright", "exciting times lie ahead")
- Made the voice more personal and less "assembled" (varied rhythm, fewer placeholders)

## Attribution

Ported from [blader/humanizer](https://github.com/blader/humanizer) (MIT), based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup. Original author: Siqi Chen ([@blader](https://github.com/blader)); original repo: https://github.com/blader/humanizer, version 2.5.1. Hermes port adds native `read_file`, `patch`, and `write_file` guidance, the loading trigger, the marketing/blog cliché list in pattern 7, and patterns 30–34. Instructional prose was lightly edited to model the guidance. Original MIT license remains in the adjacent `LICENSE` file alongside this `SKILL.md`.

Key insight from Wikipedia: "LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases."

## Pitfalls

- do not remove deliberate voice, domain terminology, factual specificity, or useful structure merely to sound less polished
- do not invent citations, people, events, or supporting facts while rewriting
- patterns are a diagnostic catalog, not a checklist that forces every passage into the same voice

## Verification

- meaning, facts, intended tone, and deliberate style survive
- all 34 pattern classes were considered; remaining tells are named before final rewrite
- final text reads naturally aloud, varies rhythm, uses specific details, and avoids unearned framing
- file edits show a diff/changed section; no invented facts or unsourced citations
