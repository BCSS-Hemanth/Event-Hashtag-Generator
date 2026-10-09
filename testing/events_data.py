"""
Test Dataset: 52 Real-World Indian Events
Spans North, South, East, West, Central, and Northeast India across diverse domains:
Politics, Education, Protests, Sports, Festivals, Technology, Environment, Government Initiatives, and Social Issues.
"""

from typing import Any, Dict, List

EVENTS_DATASET: List[Dict[str, Any]] = [
    # NORTH INDIA
    {
        "event_id": "EVT_01",
        "event_name": "Farmers Protest at Shambhu Border",
        "location": "Shambhu Border, Ambala, Haryana, Punjab",
        "state": "Punjab / Haryana",
        "region": "North",
        "category": "Protests",
        "date_context": "February - March 2024",
        "description": "Farmers marching towards New Delhi demanding a legal guarantee for Minimum Support Price (MSP), debt waiver, and pension under Samyukta Kisan Morcha (Non-Political) and Kisan Mazdoor Morcha, facing tear gas and multi-layered barricades at the Punjab-Haryana Shambhu border.",
        "reference_keywords": ["farmers protest", "shambhu border", "minimum support price", "msp guarantee", "samyukta kisan morcha", "sarwan singh pandher", "jagjit singh dallewal", "haryana police", "tear gas", "punjab"],
        "reference_hashtags": ["#FarmersProtest", "#ShambhuBorder", "#MSPGuarantee", "#FarmersProtest2024", "#KisanAndolan", "#SamyuktaKisanMorcha", "#PunjabFarmers"],
        "key_entities": {
            "people": ["Sarwan Singh Pandher", "Jagjit Singh Dallewal"],
            "organizations": ["Samyukta Kisan Morcha", "Kisan Mazdoor Morcha", "Haryana Police"],
            "locations": ["Shambhu Border", "Ambala", "Punjab", "Haryana", "Delhi"],
            "demands": ["legal guarantee for MSP", "farmer debt waiver", "pension for farmers"]
        }
    },
    {
        "event_id": "EVT_02",
        "event_name": "Delhi Air Pollution Emergency and GRAP IV",
        "location": "New Delhi, Delhi NCR",
        "state": "Delhi",
        "region": "North",
        "category": "Environment",
        "date_context": "November 2023 - November 2024",
        "description": "Severe air quality index (AQI) spike exceeding 450 in Delhi NCR triggering Stage IV of the Graded Response Action Plan (GRAP), banning diesel medium and heavy goods vehicles, halting non-essential construction, and mandating online school classes by the Commission for Air Quality Management (CAQM).",
        "reference_keywords": ["delhi air pollution", "grap iv", "air quality index", "caqm", "stubble burning", "toxic smog", "construction ban", "commission for air quality management", "delhi ncr"],
        "reference_hashtags": ["#DelhiAirPollution", "#DelhiSmog", "#GRAP4", "#DelhiAQI", "#AirQualityIndex", "#PollutionFreeDelhi", "#CAQM"],
        "key_entities": {
            "people": ["Gopal Rai"],
            "organizations": ["Commission for Air Quality Management", "CAQM", "Delhi Government"],
            "locations": ["New Delhi", "Delhi NCR", "Anand Vihar"],
            "demands": ["stubble burning control", "ban on polluting trucks", "work from home advisories"]
        }
    },
    {
        "event_id": "EVT_03",
        "event_name": "Ayodhya Ram Mandir Pran Pratishtha",
        "location": "Ayodhya, Uttar Pradesh",
        "state": "Uttar Pradesh",
        "region": "North",
        "category": "Festivals",
        "date_context": "January 22, 2024",
        "description": "Consecration ceremony of the Ram Lalla idol at the newly constructed Shri Ram Janmbhoomi Mandir in Ayodhya, attended by Prime Minister Narendra Modi, RSS Chief Mohan Bhagwat, Uttar Pradesh Chief Minister Yogi Adityanath, and thousands of dignitaries.",
        "reference_keywords": ["ayodhya ram mandir", "pran pratishtha", "shri ram janmabhoomi", "ram lalla", "narendra modi", "yogi adityanath", "mohan bhagwat", "ayodhya dham", "uttar pradesh"],
        "reference_hashtags": ["#RamMandir", "#AyodhyaRamMandir", "#PranPratishtha", "#RamLalla", "#AyodhyaDham", "#JaiShriRam", "#NarendraModi"],
        "key_entities": {
            "people": ["Narendra Modi", "Yogi Adityanath", "Mohan Bhagwat", "Nritya Gopal Das"],
            "organizations": ["Shri Ram Janmabhoomi Teerth Kshetra", "Rashtriya Swayamsevak Sangh"],
            "locations": ["Ayodhya", "Uttar Pradesh", "Saryu River"],
            "demands": ["temple consecration", "pilgrimage infrastructure"]
        }
    },
    {
        "event_id": "EVT_04",
        "event_name": "Joshimath Land Subsidence Crisis",
        "location": "Joshimath, Chamoli, Uttarakhand",
        "state": "Uttarakhand",
        "region": "North",
        "category": "Environment",
        "date_context": "January - February 2023",
        "description": "Geological land sinking and massive structural cracks appearing in hundreds of residential houses and hotels across nine wards of Joshimath town, prompting emergency evacuation of residents by the Chamoli district administration and protests against NTPC Tapovan Vishnugad hydro project.",
        "reference_keywords": ["joshimath sinking", "land subsidence", "chamoli", "uttarakhand", "ntpc hydro project", "cracked houses", "disaster management", "evacuation", "himalayan ecology"],
        "reference_hashtags": ["#SaveJoshimath", "#JoshimathSinking", "#JoshimathCrisis", "#UttarakhandDisaster", "#Chamoli", "#HimalayanEcology"],
        "key_entities": {
            "people": ["Pushkar Singh Dhami", "Atul Sati"],
            "organizations": ["Joshimath Bachao Sangharsh Samiti", "NTPC", "NDRF", "Chamoli District Administration"],
            "locations": ["Joshimath", "Chamoli", "Uttarakhand", "Tapovan"],
            "demands": ["permanent rehabilitation package", "halt to NTPC tunneling", "demolition compensation"]
        }
    },
    {
        "event_id": "EVT_05",
        "event_name": "G20 Tourism Working Group in Srinagar",
        "location": "SKICC, Srinagar, Jammu and Kashmir",
        "state": "Jammu and Kashmir",
        "region": "North",
        "category": "Public Affairs",
        "date_context": "May 22-24, 2023",
        "description": "The 3rd G20 Tourism Working Group meeting hosted at the Sher-i-Kashmir International Conference Centre (SKICC) along Dal Lake in Srinagar, focusing on eco-tourism, green tourism, and film tourism in the Kashmir Valley under tight multi-tier security.",
        "reference_keywords": ["g20 srinagar", "tourism working group", "dal lake", "skicc", "kashmir tourism", "manoj sinha", "green tourism", "film tourism", "jammu and kashmir"],
        "reference_hashtags": ["#G20Srinagar", "#G20India", "#KashmirTourism", "#SKICC", "#SrinagarG20", "#ExploreKashmir"],
        "key_entities": {
            "people": ["Manoj Sinha", "G. Kishan Reddy", "Amitabh Kant"],
            "organizations": ["Ministry of Tourism", "Jammu and Kashmir Administration", "G20 Secretariat"],
            "locations": ["Srinagar", "Dal Lake", "SKICC", "Jammu and Kashmir"],
            "demands": ["film shooting revival", "sustainable tourism promotion", "artisan market linkage"]
        }
    },
    {
        "event_id": "EVT_06",
        "event_name": "Khelo India Winter Games in Gulmarg",
        "location": "Gulmarg, Baramulla, Jammu and Kashmir",
        "state": "Jammu and Kashmir",
        "region": "North",
        "category": "Sports",
        "date_context": "February 2024",
        "description": "The 4th edition of Khelo India Winter Games held across snow-clad slopes of Gulmarg, featuring alpine skiing, snowboarding, ski mountaineering, and snowshoe racing with participation from over 800 athletes representing defense forces and states across India.",
        "reference_keywords": ["khelo india winter games", "gulmarg", "alpine skiing", "snowboarding", "winter sports", "baramulla", "sports authority of india", "jammu and kashmir"],
        "reference_hashtags": ["#KheloIndiaWinterGames", "#Gulmarg", "#WinterSports", "#KheloIndia", "#SkiGulmarg", "#SnowboardingIndia"],
        "key_entities": {
            "people": ["Anurag Thakur", "Manoj Sinha"],
            "organizations": ["Sports Authority of India", "Jammu and Kashmir Sports Council", "Winter Games Association"],
            "locations": ["Gulmarg", "Baramulla", "Jammu and Kashmir", "Kongdoori"],
            "demands": ["winter sports infrastructure", "olympic training facilities"]
        }
    },
    {
        "event_id": "EVT_07",
        "event_name": "Shimla Urban Water Crisis and Tourism Impact",
        "location": "The Mall, Shimla, Himachal Pradesh",
        "state": "Himachal Pradesh",
        "region": "North",
        "category": "Public Affairs",
        "date_context": "May - June 2023",
        "description": "Acute drinking water rationing and drying up of natural catchment sources including Gumma and Giri pumping stations in Shimla during peak summer tourist influx, leading to citizen protests and hotel occupancy drops.",
        "reference_keywords": ["shimla water crisis", "drinking water rationing", "gumma pumping station", "shimla municipal corporation", "himachal pradesh", "tourist season", "giri water scheme"],
        "reference_hashtags": ["#ShimlaWaterCrisis", "#SaveShimla", "#ShimlaTourism", "#WaterConservation", "#HimachalPradesh"],
        "key_entities": {
            "people": ["Sukhvinder Singh Sukhu"],
            "organizations": ["Shimla Jal Prabandhan Nigam Limited", "Shimla Municipal Corporation"],
            "locations": ["Shimla", "The Mall", "Gumma", "Himachal Pradesh"],
            "demands": ["regular water supply", "check on tanker exploitation", "new pipeline infrastructure"]
        }
    },
    {
        "event_id": "EVT_08",
        "event_name": "Khatkar Toll Plaza Protests in Jind",
        "location": "Khatkar Toll Plaza, Jind, Haryana",
        "state": "Haryana",
        "region": "North",
        "category": "Protests",
        "date_context": "March 2024",
        "description": "Farmer groups, youth, and khap panchayats staged sit-in dharnas at Khatkar Toll Plaza on the Jind-Patiala highway to protest the detention of farmer union activists and demand free passage for tractors.",
        "reference_keywords": ["khatkar toll plaza", "jind protest", "khap panchayat", "bharat kisan union", "highway blockade", "haryana farmers", "tractor march"],
        "reference_hashtags": ["#KhatkarTollPlaza", "#JindProtest", "#HaryanaFarmers", "#KisanEkta", "#KhapPanchayat"],
        "key_entities": {
            "people": ["Rakesh Tikait", "Gurnam Singh Charuni"],
            "organizations": ["Khatkar Toll Committee", "Bharatiya Kisan Union", "Sarv Khap Panchayat"],
            "locations": ["Khatkar Toll Plaza", "Jind", "Haryana"],
            "demands": ["release of detained activists", "waiver of toll for local farmers"]
        }
    },
    {
        "event_id": "EVT_09",
        "event_name": "Maha Kumbh Mela Preparations in Prayagraj",
        "location": "Sangam, Prayagraj, Uttar Pradesh",
        "state": "Uttar Pradesh",
        "region": "North",
        "category": "Festivals",
        "date_context": "October 2024 - January 2025",
        "description": "Massive civic infrastructure, tent cities, ghat renovations, and crowd control setups undertaken by the Uttar Pradesh state government across Triveni Sangam in Prayagraj for the upcoming Maha Kumbh Mela congregation expected to draw 400 million pilgrims.",
        "reference_keywords": ["maha kumbh mela", "prayagraj sangam", "triveni sangam", "kumbh 2025", "uttar pradesh tourism", "tent city", "snan ghats", "yogi adityanath"],
        "reference_hashtags": ["#MahaKumbh2025", "#PrayagrajKumbh", "#TriveniSangam", "#KumbhMela", "#DivyaKumbh"],
        "key_entities": {
            "people": ["Yogi Adityanath"],
            "organizations": ["Kumbh Mela Administration", "Uttar Pradesh Tourism", "Prayagraj Mela Pradhikaran"],
            "locations": ["Prayagraj", "Triveni Sangam", "Uttar Pradesh"],
            "demands": ["sanitation infrastructure", "clean ganga flow", "green energy transport"]
        }
    },
    {
        "event_id": "EVT_10",
        "event_name": "Kashi Vishwanath Corridor Pilgrimage Surge",
        "location": "Varanasi, Uttar Pradesh",
        "state": "Uttar Pradesh",
        "region": "North",
        "category": "Government Initiatives",
        "date_context": "July - August 2024",
        "description": "Record footfall of Sawan pilgrims and devotees visiting the transformed Kashi Vishwanath Dham Corridor connecting the Ganga ghats with the sanctum sanctorum in Varanasi, managed with dedicated queue lanes and drone surveillance.",
        "reference_keywords": ["kashi vishwanath corridor", "varanasi pilgrimage", "kashi vishwanath dham", "ganga ghats", "sawan mela", "narendra modi", "uttar pradesh"],
        "reference_hashtags": ["#KashiVishwanath", "#Varanasi", "#KashiDham", "#GangaGhats", "#HarHarMahadev"],
        "key_entities": {
            "people": ["Narendra Modi", "Yogi Adityanath"],
            "organizations": ["Kashi Vishwanath Temple Trust", "Varanasi Police"],
            "locations": ["Varanasi", "Kashi", "Dashashwamedh Ghat", "Uttar Pradesh"],
            "demands": ["crowd management", "accessible darshan for elderly"]
        }
    },

    # SOUTH INDIA
    {
        "event_id": "EVT_11",
        "event_name": "Bengaluru Tech Summit 2024",
        "location": "Bangalore Palace, Bengaluru, Karnataka",
        "state": "Karnataka",
        "region": "South",
        "category": "Technology",
        "date_context": "November 19-21, 2024",
        "description": "The 27th edition of Bengaluru Tech Summit (BTS) organized by the Department of Electronics, IT and BT, Government of Karnataka at Bangalore Palace, uniting tech founders, unicorn CEOs, venture capitalists, and delegates from 40 countries to showcase artificial intelligence, biotech, semiconductors, and deep-tech innovations.",
        "reference_keywords": ["bengaluru tech summit", "bts 2024", "karnataka it", "artificial intelligence", "deep tech", "bangalore palace", "biotechnology", "semiconductors", "siddaramaiah"],
        "reference_hashtags": ["#BTS2024", "#BengaluruTechSummit", "#BangaloreTech", "#KarnatakaIT", "#DeepTech", "#InnovateKarnataka"],
        "key_entities": {
            "people": ["Siddaramaiah", "D.K. Shivakumar", "Priyank Kharge"],
            "organizations": ["Department of IT BT Karnataka", "Karnataka Innovation and Technology Society", "NASSCOM"],
            "locations": ["Bengaluru", "Bangalore Palace", "Karnataka"],
            "demands": ["start-up funding policies", "GCC global capability centers expansion"]
        }
    },
    {
        "event_id": "EVT_12",
        "event_name": "Cauvery Water Dispute Bandh in Bengaluru",
        "location": "Bengaluru, Mandya, Karnataka",
        "state": "Karnataka",
        "region": "South",
        "category": "Protests",
        "date_context": "September - October 2023",
        "description": "Total statewide dawn-to-dusk Karnataka Bandh and Bengaluru Bandh called by Kannada Okkuta and farmer organisations protesting against the Cauvery Water Management Authority (CWMA) directive ordering release of Cauvery river water to Tamil Nadu amid severe drought in the basin.",
        "reference_keywords": ["cauvery water dispute", "karnataka bandh", "bengaluru bandh", "cwma", "cauvery river", "kannada okkuta", "vatal nagaraj", "mandya farmers", "tamil nadu"],
        "reference_hashtags": ["#CauveryWaterDispute", "#KarnatakaBandh", "#BengaluruBandh", "#SaveCauveryWater", "#CauveryProtest"],
        "key_entities": {
            "people": ["Vatal Nagaraj", "Siddaramaiah", "M.K. Stalin"],
            "organizations": ["Kannada Okkuta", "Karnataka Rajya Raitha Sangha", "Cauvery Water Management Authority"],
            "locations": ["Bengaluru", "Mandya", "Mysuru", "Karnataka", "Tamil Nadu"],
            "demands": ["halt water release to Tamil Nadu", "distress sharing formula review"]
        }
    },
    {
        "event_id": "EVT_13",
        "event_name": "Aero India Air Show at Yelahanka",
        "location": "Air Force Station Yelahanka, Bengaluru, Karnataka",
        "state": "Karnataka",
        "region": "South",
        "category": "Technology",
        "date_context": "February 13-17, 2023",
        "description": "Asia's premier biennial aerospace exhibition Aero India held at Yelahanka Air Force Station showcasing indigenous Tejas light combat aircraft, DRDO drones, BrahMos missiles, and defense flight aerobatic maneuvers.",
        "reference_keywords": ["aero india", "yelahanka air base", "tejas aircraft", "drdo", "defense aerospace", "aerobatics", "hal", "bengaluru aviation"],
        "reference_hashtags": ["#AeroIndia", "#AeroIndia2023", "#MakeInIndiaDefence", "#TejasLCA", "#YelahankaAirShow"],
        "key_entities": {
            "people": ["Narendra Modi", "Rajnath Singh"],
            "organizations": ["Ministry of Defence", "Hindustan Aeronautics Limited", "DRDO", "Indian Air Force"],
            "locations": ["Bengaluru", "Yelahanka", "Karnataka"],
            "demands": ["indigenous defense manufacturing", "export agreements"]
        }
    },
    {
        "event_id": "EVT_14",
        "event_name": "Jallikattu Bull Taming Festival in Alanganallur",
        "location": "Alanganallur, Madurai, Tamil Nadu",
        "state": "Tamil Nadu",
        "region": "South",
        "category": "Festivals",
        "date_context": "January 14-17, 2024",
        "description": "Traditional Pongal sport Jallikattu bull-taming championship conducted at Alanganallur, Palamedu, and Avaniyapuram in Madurai, with hundreds of tamers competing in the arena under veterinary monitoring and police safety guidelines.",
        "reference_keywords": ["jallikattu", "alanganallur", "madurai", "bull taming", "pongal festival", "tamil nadu culture", "palamedu", "avaniyapuram"],
        "reference_hashtags": ["#Jallikattu", "#AlanganallurJallikattu", "#MaduraiJallikattu", "#TamilNaduCulture", "#PongalFestival", "#VeeraVilaiyattu"],
        "key_entities": {
            "people": ["Udhayanidhi Stalin", "M.K. Stalin"],
            "organizations": ["Madurai District Administration", "Tamil Nadu Animal Husbandry Department"],
            "locations": ["Alanganallur", "Madurai", "Palamedu", "Tamil Nadu"],
            "demands": ["safety protocols", "native bull breed conservation"]
        }
    },
    {
        "event_id": "EVT_15",
        "event_name": "Ennore Creek Oil Spill Environmental Disaster",
        "location": "Ennore Creek, Kosasthalaiyar River, Chennai, Tamil Nadu",
        "state": "Tamil Nadu",
        "region": "South",
        "category": "Environment",
        "date_context": "December 2023",
        "description": "Massive furnace oil leakage from Chennai Petroleum Corporation Limited (CPCL) refinery following Cyclone Michaung flooding into Kosasthalaiyar River and Ennore Creek, destroying mangrove swamps and fishing livelihood.",
        "reference_keywords": ["ennore oil spill", "kosasthalaiyar river", "cpcl refinery", "cyclone michaung", "chennai oil spill", "pollution control board", "fishermen compensation"],
        "reference_hashtags": ["#EnnoreOilSpill", "#SaveEnnoreCreek", "#ChennaiOilSpill", "#ClimateJusticeChennai", "#EnnoreDisaster"],
        "key_entities": {
            "people": ["M.K. Stalin", "Poovulagin Nanbargal"],
            "organizations": ["Chennai Petroleum Corporation Limited", "CPCL", "Tamil Nadu Pollution Control Board", "Coast Guard"],
            "locations": ["Ennore Creek", "Kosasthalaiyar River", "Chennai", "Tamil Nadu"],
            "demands": ["immediate oil recovery", "fair compensation for fisherfolk", "wetland restoration"]
        }
    },
    {
        "event_id": "EVT_16",
        "event_name": "Formula 4 Indian Street Circuit Night Race",
        "location": "Island Grounds, Chennai, Tamil Nadu",
        "state": "Tamil Nadu",
        "region": "South",
        "category": "Sports",
        "date_context": "August 31 - September 1, 2024",
        "description": "South Asia's first night street circuit motor race featuring FIA Formula 4 Indian Championship and Indian Racing League conducted across a 3.5 km street track around Island Grounds and Marina Beach in Chennai.",
        "reference_keywords": ["formula 4 chennai", "night street circuit", "island grounds", "motorsport india", "racing promotions private limited", "udhayanidhi stalin", "chennai street circuit"],
        "reference_hashtags": ["#ChennaiFormula4", "#F4India", "#StreetCircuitChennai", "#NightRaceChennai", "#MotorsportIndia"],
        "key_entities": {
            "people": ["Udhayanidhi Stalin"],
            "organizations": ["Sports Development Authority of Tamil Nadu", "Racing Promotions Private Limited", "FIA"],
            "locations": ["Chennai", "Island Grounds", "Marina Beach", "Tamil Nadu"],
            "demands": ["fia track certification", "public traffic mitigation"]
        }
    },
    {
        "event_id": "EVT_17",
        "event_name": "Wayanad Landslides Disaster and Relief",
        "location": "Chooralmala, Meppadi, Wayanad, Kerala",
        "state": "Kerala",
        "region": "South",
        "category": "Environment",
        "date_context": "July 30, 2024",
        "description": "Catastrophic midnight landslides triggered by torrential monsoon rain wiping out the villages of Chooralmala and Mundakkai in Meppadi panchayat of Wayanad, claiming over 300 lives and mobilizing large-scale Indian Army rescue bridges and NDRF operations.",
        "reference_keywords": ["wayanad landslides", "chooralmala", "mundakkai", "meppadi", "pinarayi vijayan", "ndrf rescue", "bailey bridge", "kerala disaster", "landslide relief"],
        "reference_hashtags": ["#WayanadLandslides", "#StandWithWayanad", "#WayanadDisaster", "#Chooralmala", "#KeralaRelief", "#RescueWayanad"],
        "key_entities": {
            "people": ["Pinarayi Vijayan", "Rahul Gandhi", "Major General V.T. Mathew"],
            "organizations": ["Indian Army", "NDRF", "Kerala State Disaster Management Authority", "Territorial Army"],
            "locations": ["Wayanad", "Chooralmala", "Mundakkai", "Meppadi", "Kerala"],
            "demands": ["national disaster declaration", "comprehensive township rehabilitation", "climate resilient zoning"]
        }
    },
    {
        "event_id": "EVT_18",
        "event_name": "Thrissur Pooram Festival and Kudamattom",
        "location": "Vadakkunnathan Temple, Thekkinkadu Maidan, Thrissur, Kerala",
        "state": "Kerala",
        "region": "South",
        "category": "Festivals",
        "date_context": "April 19-20, 2024",
        "description": "The mother of all temple festivals in Kerala featuring the magnificent face-off Kudamattom umbrella exchange between Paramekkavu and Thiruvambady devaswoms, alongside traditional Ilanjithara Melam percussion orchestra at Thekkinkadu Maidan.",
        "reference_keywords": ["thrissur pooram", "kudamattom", "thekkinkadu maidan", "paramekkavu", "thiruvambady", "ilanjithara melam", "vadakkumnathan", "kerala festivals"],
        "reference_hashtags": ["#ThrissurPooram", "#Pooram2024", "#Kudamattom", "#IlanjitharaMelam", "#KeralaFestival", "#Thrissur"],
        "key_entities": {
            "people": ["K. Radhakrishnan"],
            "organizations": ["Paramekkavu Devaswom", "Thiruvambady Devaswom", "Cochin Devaswom Board", "Thrissur District Police"],
            "locations": ["Thrissur", "Thekkinkadu Maidan", "Vadakkunnathan Temple", "Kerala"],
            "demands": ["fireworks clearance without disruption", "crowd barrier adjustments"]
        }
    },
    {
        "event_id": "EVT_19",
        "event_name": "Kochi-Muziris Biennale Contemporary Art Exhibition",
        "location": "Fort Kochi, Mattancherry, Kochi, Kerala",
        "state": "Kerala",
        "region": "South",
        "category": "Social Issues",
        "date_context": "December 2022 - April 2023",
        "description": "International contemporary art biennale held across heritage warehouses, Aspinwall House, and sea-facing venues in Fort Kochi, showcasing artworks, installations, and seminars by global artists.",
        "reference_keywords": ["kochi biennale", "kochi muziris biennale", "fort kochi", "contemporary art", "aspinwall house", "shubigi rao", "kerala tourism"],
        "reference_hashtags": ["#KochiBiennale", "#KochiMuzirisBiennale", "#FortKochi", "#ContemporaryArt", "#Biennale2023"],
        "key_entities": {
            "people": ["Bose Krishnamachari", "Shubigi Rao"],
            "organizations": ["Kochi Biennale Foundation", "Kerala Tourism Department"],
            "locations": ["Fort Kochi", "Mattancherry", "Aspinwall House", "Kochi", "Kerala"],
            "demands": ["permanent heritage conservation", "arts education support"]
        }
    },
    {
        "event_id": "EVT_20",
        "event_name": "Global AI Summit at HICC Hyderabad",
        "location": "HICC Novotel, Hitec City, Hyderabad, Telangana",
        "state": "Telangana",
        "region": "South",
        "category": "Technology",
        "date_context": "September 5-6, 2024",
        "description": "Flagship global artificial intelligence conference organized by the Government of Telangana at Hyderabad International Convention Centre (HICC), unveiling the Telangana AI Mission (T-AIM) road map, ethical AI frameworks, and AI City infrastructure project.",
        "reference_keywords": ["global ai summit", "hyderabad ai summit", "hicc novotel", "revanth reddy", "telangana ai mission", "artificial intelligence india", "hitec city", "ai city"],
        "reference_hashtags": ["#GlobalAISummit", "#HyderabadAI", "#TelanganaAI", "#ArtificialIntelligence", "#HICC", "#AICityHyderabad"],
        "key_entities": {
            "people": ["A. Revanth Reddy", "D. Sridhar Babu"],
            "organizations": ["Telangana IT Department", "T-AIM", "NASSCOM", "World Economic Forum"],
            "locations": ["Hyderabad", "HICC", "Hitec City", "Telangana"],
            "demands": ["ethical AI regulatory framework", "200 acre AI City establishment"]
        }
    },
    {
        "event_id": "EVT_21",
        "event_name": "Hyderabad E-Prix Formula E Championship",
        "location": "NTR Marg, Hussain Sagar, Hyderabad, Telangana",
        "state": "Telangana",
        "region": "South",
        "category": "Sports",
        "date_context": "February 11, 2023",
        "description": "India's first all-electric FIA Formula E World Championship street circuit held alongside the Hussain Sagar lake and Secretariat in Hyderabad, featuring international electric racing teams like Mahindra Racing, Jaguar, and Porsche.",
        "reference_keywords": ["hyderabad e prix", "formula e hyderabad", "ntr marg", "hussain sagar", "electric racing", "mahindra racing", "fia formula e"],
        "reference_hashtags": ["#HyderabadEPrix", "#FormulaEIndia", "#GreenRacing", "#HussainSagar", "#FormulaE"],
        "key_entities": {
            "people": ["K.T. Rama Rao", "Jean Todt"],
            "organizations": ["Formula E Operations", "Mahindra Racing", "Telangana Tourism"],
            "locations": ["Hyderabad", "NTR Marg", "Hussain Sagar", "Telangana"],
            "demands": ["sustainable electric mobility adoption", "civic disruption minimisation"]
        }
    },
    {
        "event_id": "EVT_22",
        "event_name": "Bonalu Festival Celebrations in Hyderabad",
        "location": "Golconda Fort, Lal Darwaza, Hyderabad, Telangana",
        "state": "Telangana",
        "region": "South",
        "category": "Festivals",
        "date_context": "July 2024",
        "description": "Traditional Ashada Bonalu folk festival worshipping Goddess Mahakali across historic Golconda Fort, Secunderabad Ujjaini Mahakali temple, and Old City Lal Darwaza with decorated earthen pots and Pothuraju dances.",
        "reference_keywords": ["bonalu festival", "hyderabad bonalu", "golconda fort", "lal darwaza", "mahakali temple", "pothuraju", "telangana festivals", "ujjaini mahakali"],
        "reference_hashtags": ["#BonaluFestival", "#HyderabadBonalu", "#GolcondaBonalu", "#TelanganaCulture", "#Bonalu2024"],
        "key_entities": {
            "people": ["Revanth Reddy", "Konda Surekha"],
            "organizations": ["Telangana Endowments Department", "Lal Darwaza Temple Committee"],
            "locations": ["Hyderabad", "Golconda Fort", "Secunderabad", "Lal Darwaza", "Telangana"],
            "demands": ["state festival budget grant", "security at crowded temples"]
        }
    },
    {
        "event_id": "EVT_23",
        "event_name": "Chandrayaan-3 Moon Mission Launch",
        "location": "Satish Dhawan Space Centre, Sriharikota, Andhra Pradesh",
        "state": "Andhra Pradesh",
        "region": "South",
        "category": "Technology",
        "date_context": "July 14, 2023",
        "description": "Historic launch of ISRO's Chandrayaan-3 lunar exploration mission aboard the LVM3-M4 rocket from Satish Dhawan Space Centre in Sriharikota, leading to the successful soft landing of the Vikram lander on the Moon's South Pole.",
        "reference_keywords": ["chandrayaan 3", "sriharikota launch", "isro", "lvm3 rocket", "vikram lander", "pragyan rover", "s somanath", "moon mission", "andhra pradesh"],
        "reference_hashtags": ["#Chandrayaan3", "#ISRO", "#IndiaOnTheMoon", "#Sriharikota", "#LVM3", "#SpaceExploration"],
        "key_entities": {
            "people": ["S. Somanath", "P. Veeramuthuvel", "Narendra Modi"],
            "organizations": ["Indian Space Research Organisation", "ISRO", "Satish Dhawan Space Centre"],
            "locations": ["Sriharikota", "Tirupati", "Andhra Pradesh"],
            "demands": ["lunar south pole research", "space program budget expansion"]
        }
    },
    {
        "event_id": "EVT_24",
        "event_name": "Amaravati Capital City Farmer Protests",
        "location": "Amaravati, Thullur, Andhra Pradesh",
        "state": "Andhra Pradesh",
        "region": "South",
        "category": "Politics",
        "date_context": "2023 - 2024",
        "description": "Sustained agitation and Maha Padayatra organized by the Amaravati Parirakshana Samithi farmers who gave land for the greenfield capital city Amaravati, opposing three-capital plans and demanding completion of core government capital infrastructure.",
        "reference_keywords": ["amaravati protest", "amaravati capital", "andhra pradesh capital", "thullur farmers", "chandrababu naidu", "ysrcp three capitals", "maha padayatra"],
        "reference_hashtags": ["#AmaravatiCapital", "#SaveAmaravati", "#AmaravatiFarmers", "#AndhraPradeshPolitics", "#AmaravatiProtest"],
        "key_entities": {
            "people": ["N. Chandrababu Naidu", "Y.S. Jagan Mohan Reddy", "Siva Reddy"],
            "organizations": ["Amaravati Parirakshana Samithi", "AP Capital Region Development Authority", "APCRDA"],
            "locations": ["Amaravati", "Thullur", "Vijayawada", "Guntur", "Andhra Pradesh"],
            "demands": ["single capital city status", "resumption of high court and secretariat construction"]
        }
    },

    # WEST INDIA
    {
        "event_id": "EVT_25",
        "event_name": "Maratha Reservation Morcha in Mumbai",
        "location": "Azad Maidan, Mumbai, Maharashtra",
        "state": "Maharashtra",
        "region": "West",
        "category": "Protests",
        "date_context": "January 2024",
        "description": "Massive hunger strike and protest march led by activist Manoj Jarange Patil demanding OBC Kunbi caste certificates for the Maratha community, culminating in thousands assembling at Azad Maidan and Vashi.",
        "reference_keywords": ["maratha reservation", "manoj jarange patil", "azad maidan", "mumbai morcha", "kunbi caste certificate", "eknath shinde", "devendra fadnavis", "maharashtra politics"],
        "reference_hashtags": ["#MarathaReservation", "#ManojJarangePatil", "#MarathaMorcha", "#MumbaiProtest", "#AzadMaidan", "#MaharashtraNews"],
        "key_entities": {
            "people": ["Manoj Jarange Patil", "Eknath Shinde", "Devendra Fadnavis"],
            "organizations": ["Maratha Kranti Morcha", "Maharashtra Government"],
            "locations": ["Mumbai", "Azad Maidan", "Vashi", "Jalna", "Antarwali Sarati", "Maharashtra"],
            "demands": ["OBC status for Marathas", "Sage Soyare notification implementation"]
        }
    },
    {
        "event_id": "EVT_26",
        "event_name": "Pune Ganesh Visarjan Immersion Procession",
        "location": "Laxmi Road, Alka Talkies Chowk, Pune, Maharashtra",
        "state": "Maharashtra",
        "region": "West",
        "category": "Festivals",
        "date_context": "September 17-18, 2024",
        "description": "The grand 28-hour long Ganesh Visarjan immersion procession through historic Laxmi Road in Pune, featuring the five Manache Ganpati mandals, Dhol Tasha dhwaj pathaks, and eco-friendly immersions along Mutha river.",
        "reference_keywords": ["pune ganesh visarjan", "laxmi road", "manache ganpati", "kasba ganpati", "dhol tasha pathak", "alka talkies chowk", "mutha river", "pune police"],
        "reference_hashtags": ["#PuneGaneshotsav", "#GaneshVisarjanPune", "#LaxmiRoad", "#DholTasha", "#ManacheGanpati", "#BappaMorya"],
        "key_entities": {
            "people": ["Amitesh Kumar"],
            "organizations": ["Kasba Ganpati Trust", "Dagdusheth Halwai Ganpati Trust", "Pune City Police"],
            "locations": ["Pune", "Laxmi Road", "Alka Talkies Chowk", "Maharashtra"],
            "demands": ["noise pollution regulation", "procession time limits compliance"]
        }
    },
    {
        "event_id": "EVT_27",
        "event_name": "Mumbai Coastal Road Project Inauguration",
        "location": "Marine Drive to Worli, Mumbai, Maharashtra",
        "state": "Maharashtra",
        "region": "West",
        "category": "Government Initiatives",
        "date_context": "March 11, 2024",
        "description": "Opening of Phase 1 of the high-speed Mumbai Coastal Road (Dharmveer Swarajya Rakshak Chhatrapati Sambhaji Maharaj Coastal Road) connecting Marine Drive with Worli via India's first twin undersea tunnels beneath the Arabian Sea.",
        "reference_keywords": ["mumbai coastal road", "marine drive to worli", "undersea tunnel", "eknath shinde", "bmc", "traffic decongestion", "maharashtra infrastructure"],
        "reference_hashtags": ["#MumbaiCoastalRoad", "#CoastalRoadMumbai", "#MarineDrive", "#MumbaiInfrastructure", "#BMC", "#AamchiMumbai"],
        "key_entities": {
            "people": ["Eknath Shinde", "Devendra Fadnavis", "Ajit Pawar"],
            "organizations": ["Brihanmumbai Municipal Corporation", "BMC", "L&T"],
            "locations": ["Mumbai", "Marine Drive", "Worli", "Bandra", "Maharashtra"],
            "demands": ["toll-free transit period", "pedestrian sea-promenade completion"]
        }
    },
    {
        "event_id": "EVT_28",
        "event_name": "Vibrant Gujarat Global Summit in Gandhinagar",
        "location": "Mahatma Mandir, Gandhinagar, Gujarat",
        "state": "Gujarat",
        "region": "West",
        "category": "Technology",
        "date_context": "January 10-12, 2024",
        "description": "The 10th edition of Vibrant Gujarat Global Summit at Mahatma Mandir in Gandhinagar, themed 'Gateway to the Future', with participation from global heads of state, Fortune 500 CEOs, and investment MOUs signed in semiconductor fabrication and green hydrogen.",
        "reference_keywords": ["vibrant gujarat", "gandhinagar summit", "mahatma mandir", "bhupendra patel", "narendra modi", "global investment", "semiconductors", "gift city"],
        "reference_hashtags": ["#VibrantGujarat2024", "#VibrantGujarat", "#InvestInGujarat", "#Gandhinagar", "#GatewayToTheFuture", "#MakeInIndia"],
        "key_entities": {
            "people": ["Narendra Modi", "Bhupendra Patel", "Mukesh Ambani", "Gautam Adani"],
            "organizations": ["Gujarat Industrial Development Corporation", "CII", "FICCI"],
            "locations": ["Gandhinagar", "Mahatma Mandir", "GIFT City", "Gujarat"],
            "demands": ["fast-track industrial clearances", "semiconductor subsidies"]
        }
    },
    {
        "event_id": "EVT_29",
        "event_name": "International Kite Festival Uttarayan in Ahmedabad",
        "location": "Sabarmati Riverfront, Ahmedabad, Gujarat",
        "state": "Gujarat",
        "region": "West",
        "category": "Festivals",
        "date_context": "January 7-14, 2024",
        "description": "The annual International Kite Festival (Uttarayan) along the Sabarmati Riverfront in Ahmedabad, drawing master kite flyers from 55 countries showcasing artistic kites, followed by night-flying tukkal lanterns.",
        "reference_keywords": ["international kite festival", "uttarayan ahmedabad", "sabarmati riverfront", "patang bazi", "gujarat tourism", "manja safety", "kite flying"],
        "reference_hashtags": ["#KiteFestivalAhmedabad", "#Uttarayan2024", "#SabarmatiRiverfront", "#GujaratTourism", "#KaiPoChe"],
        "key_entities": {
            "people": ["Bhupendra Patel", "Mulubhai Bera"],
            "organizations": ["Gujarat Tourism Corporation", "Ahmedabad Municipal Corporation"],
            "locations": ["Ahmedabad", "Sabarmati Riverfront", "Gujarat"],
            "demands": ["ban on synthetic nylon manja", "bird rescue camps"]
        }
    },
    {
        "event_id": "EVT_30",
        "event_name": "National Unity Day Rashtriya Ekta Diwas",
        "location": "Statue of Unity, Kevadia, Narmada, Gujarat",
        "state": "Gujarat",
        "region": "West",
        "category": "Public Affairs",
        "date_context": "October 31, 2023",
        "description": "Celebration of Sardar Vallabhbhai Patel's birth anniversary as Rashtriya Ekta Diwas at the Statue of Unity in Kevadia (Ekta Nagar), featuring an integrated parade by central armed police forces and air force flypasts.",
        "reference_keywords": ["rashtriya ekta diwas", "statue of unity", "sardar vallabhbhai patel", "kevadia", "ekta nagar", "narendra modi", "national unity day", "narmada"],
        "reference_hashtags": ["#RashtriyaEktaDiwas", "#StatueOfUnity", "#SardarPatel", "#NationalUnityDay", "#EktaNagar", "#NarendraModi"],
        "key_entities": {
            "people": ["Narendra Modi", "Sardar Vallabhbhai Patel"],
            "organizations": ["Sardar Vallabhbhai Patel Rashtriya Ekta Trust", "Ministry of Home Affairs", "CRPF"],
            "locations": ["Kevadia", "Ekta Nagar", "Narmada", "Gujarat"],
            "demands": ["national integration pledge", "eco-friendly tourism in Kevadia"]
        }
    },
    {
        "event_id": "EVT_31",
        "event_name": "Jaipur Literature Festival at Hotel Clarks Amer",
        "location": "Hotel Clarks Amer, Jaipur, Rajasthan",
        "state": "Rajasthan",
        "region": "West",
        "category": "Social Issues",
        "date_context": "February 1-5, 2024",
        "description": "The 17th edition of the iconic Jaipur Literature Festival (JLF) hosting Nobel laureates, Booker Prize winners, historians, and literary enthusiasts to debate literature, democracy, artificial intelligence, and history.",
        "reference_keywords": ["jaipur literature festival", "jlf 2024", "clarks amer", "william dalrymple", "namita gokhale", "rajasthan literature", "booker prize", "authors"],
        "reference_hashtags": ["#JLF2024", "#JaipurLitFest", "#LiteratureFestival", "#JaipurLiteratureFestival", "#BooksOfJLF"],
        "key_entities": {
            "people": ["William Dalrymple", "Namita Gokhale", "Sanjoy K. Roy"],
            "organizations": ["Teamwork Arts", "Rajasthan Tourism"],
            "locations": ["Jaipur", "Hotel Clarks Amer", "Rajasthan"],
            "demands": ["free speech protections", "inclusive vernacular translation awards"]
        }
    },
    {
        "event_id": "EVT_32",
        "event_name": "Pushkar International Camel and Livestock Fair",
        "location": "Pushkar Mela Ground, Ajmer, Rajasthan",
        "state": "Rajasthan",
        "region": "West",
        "category": "Festivals",
        "date_context": "November 2023",
        "description": "One of the world's largest livestock trading fairs held around holy Pushkar Lake, featuring decorated camel trading competitions, traditional turban-tying contests, and folk music concerts.",
        "reference_keywords": ["pushkar camel fair", "pushkar mela", "ajmer rajasthan", "camel trading", "pushkar lake", "rajasthan folk tourism", "livestock fair"],
        "reference_hashtags": ["#PushkarFair", "#PushkarMela", "#RajasthanTourism", "#IncredibleIndia", "#PushkarCamelFair"],
        "key_entities": {
            "people": ["Diya Kumari"],
            "organizations": ["Rajasthan Tourism Development Corporation", "Animal Husbandry Department"],
            "locations": ["Pushkar", "Ajmer", "Rajasthan"],
            "demands": ["veterinary health checks", "protection of camel breeders livelihood"]
        }
    },
    {
        "event_id": "EVT_33",
        "event_name": "Kota Coaching Center Student Safety Framework",
        "location": "Kota, Rajasthan",
        "state": "Rajasthan",
        "region": "West",
        "category": "Education",
        "date_context": "September - October 2023",
        "description": "Statewide guidelines and suicide prevention measures implemented by the Rajasthan Higher Education Department in Kota coaching hubs, introducing mandatory anti-hanging ceiling fan springs, psychological counseling, and mandatory recreational days for NEET and JEE aspirants.",
        "reference_keywords": ["kota coaching crisis", "neet jee aspirants", "student safety guidelines", "anti hanging device", "psychological counseling", "kota district administration", "rajasthan education"],
        "reference_hashtags": ["#KotaCoaching", "#StudentMentalHealth", "#KotaStudents", "#NEETAspirants", "#JEEPreparation", "#SaveStudents"],
        "key_entities": {
            "people": ["Om Birla", "Ashok Gehlot"],
            "organizations": ["Kota District Administration", "Rajasthan Police", "Allen Career Institute", "Resonance"],
            "locations": ["Kota", "Rajasthan"],
            "demands": ["coaching fee regulation", "decompression recreational breaks", "24x7 student helpline"]
        }
    },
    {
        "event_id": "EVT_34",
        "event_name": "International Film Festival of India (IFFI) in Goa",
        "location": "Panaji, Goa",
        "state": "Goa",
        "region": "West",
        "category": "Social Issues",
        "date_context": "November 20-28, 2023",
        "description": "The 54th International Film Festival of India held in Panaji, honoring global cinema, conferring the Satyajit Ray Lifetime Achievement Award to Michael Douglas, and showcasing regional Indian panorama films.",
        "reference_keywords": ["iffi goa", "international film festival of india", "panaji", "satyajit ray award", "michael douglas", "indian panorama", "cinema festival goa"],
        "reference_hashtags": ["#IFFI54", "#IFFIGoa", "#IndianCinema", "#GoaFilmFestival", "#WorldCinema"],
        "key_entities": {
            "people": ["Anurag Thakur", "Pramod Sawant", "Michael Douglas"],
            "organizations": ["National Film Development Corporation", "NFDC", "Entertainment Society of Goa"],
            "locations": ["Panaji", "Goa"],
            "demands": ["regional cinema OTT subsidies", "film restoration initiatives"]
        }
    },

    # EAST INDIA
    {
        "event_id": "EVT_35",
        "event_name": "RG Kar Hospital Doctors Strike in Kolkata",
        "location": "RG Kar Medical College, Shyambazar, Kolkata, West Bengal",
        "state": "West Bengal",
        "region": "East",
        "category": "Protests",
        "date_context": "August - October 2024",
        "description": "Massive public protests, 'Reclaim the Night' vigils, and an indefinite cease-work strike by West Bengal Junior Doctors Front following the brutal rape and murder of a postgraduate trainee doctor inside RG Kar Medical College seminar room.",
        "reference_keywords": ["rg kar hospital", "kolkata doctors protest", "reclaim the night", "west bengal junior doctors front", "cbi investigation", "mamata banerjee", "sandip ghosh", "kolkata police"],
        "reference_hashtags": ["#JusticeForRGKar", "#ReclaimTheNight", "#KolkataDoctorsProtest", "#RGKarHospital", "#StandWithDoctors", "#BengalDoctorsStrike"],
        "key_entities": {
            "people": ["Mamata Banerjee", "Sandip Ghosh", "Debasish Halder", "Aniket Mahato"],
            "organizations": ["West Bengal Junior Doctors Front", "CBI", "Indian Medical Association", "Supreme Court of India"],
            "locations": ["Kolkata", "RG Kar Medical College", "Shyambazar", "Swasthya Bhawan", "West Bengal"],
            "demands": ["CBI justice for trainee doctor", "resignation of corrupt health officials", "hospital safety audit and panic buttons"]
        }
    },
    {
        "event_id": "EVT_36",
        "event_name": "Kolkata Durga Puja Carnival along Red Road",
        "location": "Red Road, Maidan, Kolkata, West Bengal",
        "state": "West Bengal",
        "region": "East",
        "category": "Festivals",
        "date_context": "October 15, 2024",
        "description": "The annual Durga Puja Carnival organized by the Information and Cultural Affairs Department along Red Road in Kolkata, showcasing award-winning idol tableaux, Chhau dancers, and Dhak drum troupes before foreign diplomats.",
        "reference_keywords": ["durga puja carnival", "red road kolkata", "unesco intangible heritage", "mamata banerjee", "durga puja immersion", "dhak beats", "west bengal tourism"],
        "reference_hashtags": ["#DurgaPujaCarnival", "#KolkataDurgaPuja", "#RedRoadCarnival", "#UNESCOHeritage", "#PujoVibes"],
        "key_entities": {
            "people": ["Mamata Banerjee"],
            "organizations": ["Information and Cultural Affairs Department", "Kolkata Police", "Forum for Durgotsab"],
            "locations": ["Kolkata", "Red Road", "Maidan", "West Bengal"],
            "demands": ["heritage preservation", "traffic rerouting management"]
        }
    },
    {
        "event_id": "EVT_37",
        "event_name": "Darjeeling Tea Garden Minimum Wage Agitation",
        "location": "Chowrasta, Darjeeling, West Bengal",
        "state": "West Bengal",
        "region": "East",
        "category": "Social Issues",
        "date_context": "June - July 2023",
        "description": "Tea plantation workers and labor unions in Darjeeling and Terai hills launched gate meetings, strikes, and relay fasts demanding notification of statutory minimum wages under the Minimum Wages Act.",
        "reference_keywords": ["darjeeling tea crisis", "plantation workers strike", "minimum wage tea garden", "gorkha janmukti morcha", "tea board of india", "darjeeling hills"],
        "reference_hashtags": ["#DarjeelingTeaWorkers", "#TeaGardenWages", "#SaveDarjeelingTea", "#LaborRights", "#DarjeelingProtest"],
        "key_entities": {
            "people": ["Anit Thapa", "Hamro Party Leaders"],
            "organizations": ["Gorkhaland Territorial Administration", "Joint Forum of Trade Unions", "Tea Board of India"],
            "locations": ["Darjeeling", "Kurseong", "Kalimpong", "West Bengal"],
            "demands": ["daily wage hike to statutory limits", "parcha-patta land rights for laborers"]
        }
    },
    {
        "event_id": "EVT_38",
        "event_name": "Puri Jagannath Rath Yatra Festival",
        "location": "Grand Road Bada Danda, Puri, Odisha",
        "state": "Odisha",
        "region": "East",
        "category": "Festivals",
        "date_context": "July 7-8, 2024",
        "description": "The historic two-day chariot festival of Lord Jagannath, Balabhadra, and Subhadra along Grand Road (Bada Danda) from Jagannath Temple to Gundicha Temple, witnessed by over a million pilgrims under the newly elected BJP government.",
        "reference_keywords": ["puri rath yatra", "lord jagannath", "bada danda", "gundicha temple", "nandighosha chariot", "chhera panhara", "mohan charan majhi", "odisha police"],
        "reference_hashtags": ["#PuriRathYatra", "#RathYatra2024", "#JaiJagannath", "#PuriDham", "#BadaDanda", "#OdishaCulture"],
        "key_entities": {
            "people": ["Mohan Charan Majhi", "Gajapati Maharaja Dibyasingha Deb"],
            "organizations": ["Shree Jagannath Temple Administration", "SJTA", "Puri District Police"],
            "locations": ["Puri", "Bada Danda", "Gundicha Temple", "Odisha"],
            "demands": ["ratna bhandar opening inspection", "crowd heatstroke mitigation"]
        }
    },
    {
        "event_id": "EVT_39",
        "event_name": "Odisha School Textbook Controversy",
        "location": "Bhubaneswar, Odisha",
        "state": "Odisha",
        "region": "East",
        "category": "Education",
        "date_context": "September - October 2024",
        "description": "Student organisations including Navnirman Yuva Chhatra Sangathan and Student Congress launched demonstrations outside the state assembly in Bhubaneswar protesting major factual errors and omissions in newly printed Class 9 history textbooks, demanding the education minister's apology.",
        "reference_keywords": ["odisha textbook controversy", "textbook errors", "school mass education", "navnirman yuva chhatra sangathan", "bhubaneswar protest", "nityananda gond", "history curriculum"],
        "reference_hashtags": ["#OdishaTextbookControversy", "#TextbookErrors", "#StudentProtestOdisha", "#SaveEducation", "#BhubaneswarProtest"],
        "key_entities": {
            "people": ["Nityananda Gond", "Saurav Das"],
            "organizations": ["Navnirman Yuva Chhatra Sangathan", "Odisha Student Congress", "Citizens for Justice and Peace"],
            "locations": ["Bhubaneswar", "Cuttack", "Odisha"],
            "demands": ["immediate error rectifications", "punitive action against textbook board authors"]
        }
    },
    {
        "event_id": "EVT_40",
        "event_name": "Make in Odisha Conclave in Bhubaneswar",
        "location": "Janata Maidan, Bhubaneswar, Odisha",
        "state": "Odisha",
        "region": "East",
        "category": "Technology",
        "date_context": "November 2022 - January 2024",
        "description": "Global investor summit organized by the Industries Department of Odisha at Janata Maidan, securing investment pledges in green steel, aluminum manufacturing, IT parks, and ports.",
        "reference_keywords": ["make in odisha", "janata maidan", "odisha industrial investment", "bhubaneswar conclave", "green steel", "invest odisha", "idco"],
        "reference_hashtags": ["#MakeInOdisha", "#InvestInOdisha", "#BhubaneswarBusiness", "#OdishaGrowth", "#JanataMaidan"],
        "key_entities": {
            "people": ["Naveen Patnaik", "Hemant Sharma"],
            "organizations": ["IPICOL", "IDCO", "Odisha Industries Department"],
            "locations": ["Bhubaneswar", "Janata Maidan", "Odisha"],
            "demands": ["single window clearance portal", "port connectivity corridors"]
        }
    },
    {
        "event_id": "EVT_41",
        "event_name": "BPSC Teacher Recruitment Aspirants Protest in Patna",
        "location": "Dak Bungalow Chowk, Gandhi Maidan, Patna, Bihar",
        "state": "Bihar",
        "region": "East",
        "category": "Education",
        "date_context": "November 2023 - March 2024",
        "description": "Thousands of primary and secondary teaching candidates protested at Dak Bungalow Crossing against domicile rule cancellation and paper leaks in Bihar Public Service Commission (BPSC TRE 3.0) recruitment examinations, facing police lathicharge.",
        "reference_keywords": ["bpsc teacher protest", "dak bungalow chowk", "bpsc tre 3", "bihar teacher recruitment", "paper leak protest", "patna police", "domicile policy bihar"],
        "reference_hashtags": ["#BPSCTeacherProtest", "#BPSC_TRE3_Cancel", "#PatnaProtest", "#BiharStudents", "#JusticeForAspirants"],
        "key_entities": {
            "people": ["Dilip Kumar", "Nitish Kumar", "Tejashwi Yadav"],
            "organizations": ["Bihar Public Service Commission", "BPSC", "Patna District Police"],
            "locations": ["Patna", "Dak Bungalow Chowk", "Gandhi Maidan", "Bihar"],
            "demands": ["cancellation of tainted exam shifts", "strict anti-paper leak law enforcement"]
        }
    },
    {
        "event_id": "EVT_42",
        "event_name": "Chhath Puja Sun Worship at Ganga Ghats in Patna",
        "location": "Collectorate Ghat, Digha Ghat, Patna, Bihar",
        "state": "Bihar",
        "region": "East",
        "category": "Festivals",
        "date_context": "November 2024",
        "description": "The four-day sacred solar folk festival Chhath Puja observed by millions of devotees offering arghya to the setting and rising Sun along the banks of River Ganga in Patna, marked by strict fasting and bamboo soop offerings.",
        "reference_keywords": ["chhath puja patna", "ganga ghats bihar", "arghya", "surya devta", "chhathi maiya", "collectorate ghat", "patna municipal corporation"],
        "reference_hashtags": ["#ChhathPuja", "#ChhathPuja2024", "#PatnaChhath", "#GangaGhats", "#BiharCulture", "#ChhathiMaiya"],
        "key_entities": {
            "people": ["Nitish Kumar"],
            "organizations": ["Patna Municipal Corporation", "Bihar State Disaster Management Authority"],
            "locations": ["Patna", "Ganga Ghats", "Collectorate Ghat", "Digha Ghat", "Bihar"],
            "demands": ["clean water barricades", "pontoon bridge crowd safety"]
        }
    },
    {
        "event_id": "EVT_43",
        "event_name": "Bihar Caste-Based Survey Report Release",
        "location": "Patna, Bihar",
        "state": "Bihar",
        "region": "East",
        "category": "Politics",
        "date_context": "October 2, 2023",
        "description": "Release of the landmark Bihar Jati Adharit Ganana (Caste-based survey) data by the Nitish Kumar government, revealing that Extremely Backward Classes (EBC) and Other Backward Classes (OBC) comprise 63% of the state's population.",
        "reference_keywords": ["bihar caste survey", "jati adharit ganana", "nitish kumar", "ebc obc reservation", "patna assembly", "social justice bihar", "caste census"],
        "reference_hashtags": ["#BiharCasteSurvey", "#JatiGanana", "#SocialJustice", "#BiharPolitics", "#CasteCensusIndia"],
        "key_entities": {
            "people": ["Nitish Kumar", "Tejashwi Yadav"],
            "organizations": ["Bihar State Cabinet", "General Administration Department"],
            "locations": ["Patna", "Bihar"],
            "demands": ["quota hike proportionate to population", "special financial packages for marginalized"]
        }
    },
    {
        "event_id": "EVT_44",
        "event_name": "Sammed Shikharji Jain Pilgrimage Protection Agitation",
        "location": "Parasnath Hill, Giridih, Jharkhand",
        "state": "Jharkhand",
        "region": "East",
        "category": "Protests",
        "date_context": "December 2022 - January 2023",
        "description": "Nationwide protests by the Jain community against the Jharkhand government and central notification designating Parasnath Hill (Shri Sammed Shikharji) as an eco-tourism and wildlife sanctuary destination, demanding it remain exclusively a holy religious pilgrimage site.",
        "reference_keywords": ["sammed shikharji", "parasnath hill", "jain protest", "giridih jharkhand", "eco tourism notification", "sacred pilgrimage", "hemant soren"],
        "reference_hashtags": ["#SaveSammedShikharji", "#ParasnathHill", "#JainPilgrimage", "#SaveShikharji", "#JharkhandNews"],
        "key_entities": {
            "people": ["Muni Sugyensagar Maharaj", "Hemant Soren", "Bhupender Yadav"],
            "organizations": ["Shri Sammed Shikharji Bachao Andolan", "Ministry of Environment Forest and Climate Change"],
            "locations": ["Parasnath Hill", "Giridih", "Madhuban", "Jharkhand"],
            "demands": ["revocation of eco-tourism tag", "ban on alcohol and meat consumption on hills"]
        }
    },
    {
        "event_id": "EVT_45",
        "event_name": "National Tribal Youth Festival in Ranchi",
        "location": "Morabadi Ground, Ranchi, Jharkhand",
        "state": "Jharkhand",
        "region": "East",
        "category": "Festivals",
        "date_context": "August 9-10, 2023",
        "description": "World Tribal Day (Adivasi Mahotsav) celebrations at Morabadi Ground in Ranchi, gathering indigenous dance troupes, traditional archers, and tribal craft artisans from 20 states.",
        "reference_keywords": ["national tribal youth festival", "adivasi mahotsav", "morabadi ground", "ranchi jharkhand", "world tribal day", "indigenous art", "tribal culture"],
        "reference_hashtags": ["#AdivasiMahotsav", "#TribalYouthFestival", "#RanchiTribalFest", "#WorldTribalDay", "#IndigenousHeritage"],
        "key_entities": {
            "people": ["Hemant Soren"],
            "organizations": ["Jharkhand Welfare Department", "TRIFED"],
            "locations": ["Ranchi", "Morabadi Ground", "Jharkhand"],
            "demands": ["Sarna religious code recognition", "forest rights title distribution"]
        }
    },

    # CENTRAL INDIA
    {
        "event_id": "EVT_46",
        "event_name": "Project Cheetah in Kuno National Park",
        "location": "Kuno National Park, Sheopur, Madhya Pradesh",
        "state": "Madhya Pradesh",
        "region": "Central",
        "category": "Environment",
        "date_context": "2023 - 2024",
        "description": "India's intercontinental wildlife translocation reintroducing African cheetahs from Namibia and South Africa into acclimatization bomas and open grasslands of Kuno National Park in Madhya Pradesh under National Tiger Conservation Authority supervision.",
        "reference_keywords": ["project cheetah", "kuno national park", "sheopur", "madhya pradesh wildlife", "african cheetahs", "namibia cheetahs", "ntca", "boma enclosure"],
        "reference_hashtags": ["#ProjectCheetah", "#KunoNationalPark", "#CheetahIsBack", "#WildlifeConservation", "#MadhyaPradesh"],
        "key_entities": {
            "people": ["Narendra Modi", "Bhupender Yadav"],
            "organizations": ["National Tiger Conservation Authority", "NTCA", "Wildlife Institute of India", "Madhya Pradesh Forest Department"],
            "locations": ["Kuno National Park", "Sheopur", "Madhya Pradesh"],
            "demands": ["mitigation of radiocollar infection deaths", "second habitat development at Gandhi Sagar"]
        }
    },
    {
        "event_id": "EVT_47",
        "event_name": "Mahakal Lok Corridor Pilgrimage Expansion",
        "location": "Mahakaleshwar Temple, Ujjain, Madhya Pradesh",
        "state": "Madhya Pradesh",
        "region": "Central",
        "category": "Government Initiatives",
        "date_context": "2023 - 2024",
        "description": "The newly inaugurated Shri Mahakal Lok Corridor surrounding the ancient Mahakaleshwar Jyotirlinga in Ujjain, featuring a 900-meter corridor of stone murals, Rudrasagar lake restoration, and electronic queue systems handling over 200,000 pilgrims daily.",
        "reference_keywords": ["mahakal lok", "mahakaleshwar temple", "ujjain jyotirlinga", "rudrasagar lake", "madhya pradesh tourism", "shri mahakal corridor", "bhasma aarti"],
        "reference_hashtags": ["#MahakalLok", "#UjjainMahakal", "#Mahakaleshwar", "#ShriMahakalLok", "#UjjainDham"],
        "key_entities": {
            "people": ["Narendra Modi", "Mohan Yadav", "Shivraj Singh Chouhan"],
            "organizations": ["Shri Mahakaleshwar Temple Management Committee", "Ujjain Smart City"],
            "locations": ["Ujjain", "Rudrasagar", "Madhya Pradesh"],
            "demands": ["statue structural integrity audit", "shuttle bus connectivity from station"]
        }
    },
    {
        "event_id": "EVT_48",
        "event_name": "Pravasi Bharatiya Divas Convention in Indore",
        "location": "Brilliant Convention Centre, Indore, Madhya Pradesh",
        "state": "Madhya Pradesh",
        "region": "Central",
        "category": "Public Affairs",
        "date_context": "January 8-10, 2023",
        "description": "The 17th Pravasi Bharatiya Divas (PBD) convention held at Brilliant Convention Centre in Indore, themed 'Diaspora: Reliable partners for India's progress in Amrit Kaal', inaugurating diaspora business pavilions and youth delegations.",
        "reference_keywords": ["pravasi bharatiya divas", "pbd indore", "brilliant convention centre", "indian diaspora", "narendra modi", "s jaishankar", "cleanest city indore"],
        "reference_hashtags": ["#PBD2023", "#PravasiBharatiyaDivas", "#IndorePBD", "#IndianDiaspora", "#AmritKaal"],
        "key_entities": {
            "people": ["Narendra Modi", "S. Jaishankar", "Mohamed Irfaan Ali"],
            "organizations": ["Ministry of External Affairs", "Madhya Pradesh Government", "CII"],
            "locations": ["Indore", "Brilliant Convention Centre", "Madhya Pradesh"],
            "demands": ["consular services digitization", "diaspora investment fast-track"]
        }
    },
    {
        "event_id": "EVT_49",
        "event_name": "Hasdeo Arand Forest Coal Mining Protests",
        "location": "Hasdeo Arand, Surguja, Korba, Chhattisgarh",
        "state": "Chhattisgarh",
        "region": "Central",
        "category": "Environment",
        "date_context": "December 2023 - January 2024",
        "description": "Tribal villagers and environmental activists launched tree-hugging chipko-style protests and foot-marches opposing large-scale tree felling for the Parsa East and Kente Basan (PEKB) phase-II coal mine expansion inside the biodiverse Hasdeo Arand forest canopy.",
        "reference_keywords": ["hasdeo arand protest", "save hasdeo", "pekb coal block", "surguja chhattisgarh", "tribal tree felling", "hasdeo forest", "alok shukla"],
        "reference_hashtags": ["#SaveHasdeo", "#SaveHasdeoForest", "#HasdeoArand", "#HasdeoProtest", "#ChhattisgarhEnvironment", "#IndigenousRights"],
        "key_entities": {
            "people": ["Alok Shukla", "Vishnu Deo Sai"],
            "organizations": ["Hasdeo Aranya Bachao Sangharsh Samiti", "Adani Enterprises", "Rajasthan Rajya Vidyut Utpadan Nigam"],
            "locations": ["Hasdeo Arand", "Surguja", "Korba", "Chhattisgarh"],
            "demands": ["immediate halt to forest tree felling", "cancellation of Parsa coal block forest clearances"]
        }
    },
    {
        "event_id": "EVT_50",
        "event_name": "Bastar Dussehra 75-Day Tribal Festival",
        "location": "Danteshwari Temple, Jagdalpur, Bastar, Chhattisgarh",
        "state": "Chhattisgarh",
        "region": "Central",
        "category": "Festivals",
        "date_context": "August - October 2024",
        "description": "The world's longest festival Bastar Dussehra celebrated over 75 days in Jagdalpur dedicated to tribal deity Goddess Danteshwari, featuring the pulling of colossal double-decker wooden chariots by thousands of Maria and Muria tribesmen without any effigy burning.",
        "reference_keywords": ["bastar dussehra", "danteshwari temple", "jagdalpur chhattisgarh", "tribal chariot festival", "muria tribe", "bastar culture", "75 day festival"],
        "reference_hashtags": ["#BastarDussehra", "#BastarTribalFest", "#DanteshwariTemple", "#Jagdalpur", "#ChhattisgarhCulture"],
        "key_entities": {
            "people": ["Vishnu Deo Sai", "Bastar Royal Family Members"],
            "organizations": ["Bastar Dussehra Committee", "Chhattisgarh Tourism Board"],
            "locations": ["Jagdalpur", "Bastar", "Dantewada", "Chhattisgarh"],
            "demands": ["tribal artisan welfare", "heritage tourism infrastructure in Bastar"]
        }
    },

    # NORTHEAST INDIA
    {
        "event_id": "EVT_51",
        "event_name": "Bihu Guinness World Record Dance Performance",
        "location": "Sarusajai Stadium, Guwahati, Assam",
        "state": "Assam",
        "region": "Northeast",
        "category": "Festivals",
        "date_context": "April 13-14, 2023",
        "description": "Over 11,000 Bihu dancers and dhol drummers assembled at Sarusajai Stadium in Guwahati to perform Bihu dance and rhythm, successfully setting two Guinness World Records in the presence of Prime Minister Narendra Modi.",
        "reference_keywords": ["bihu guinness world record", "sarusajai stadium guwahati", "himanta biswa sarma", "rongali bihu", "assam cultural festival", "bihu dancers", "dhol drum"],
        "reference_hashtags": ["#BihuWorldRecord", "#RongaliBihu", "#AssamBihuRecord", "#SarusajaiStadium", "#AwesomeAssam", "#BihuDance"],
        "key_entities": {
            "people": ["Himanta Biswa Sarma", "Narendra Modi"],
            "organizations": ["Assam Cultural Affairs Department", "Guinness World Records Team"],
            "locations": ["Guwahati", "Sarusajai Stadium", "Assam"],
            "demands": ["global cultural promotion of Assamese Bihu", "stipends for rural folk artists"]
        }
    },
    {
        "event_id": "EVT_52",
        "event_name": "Hornbill Festival at Kisama Heritage Village",
        "location": "Naga Heritage Village Kisama, Kohima, Nagaland",
        "state": "Nagaland",
        "region": "Northeast",
        "category": "Festivals",
        "date_context": "December 1-10, 2023",
        "description": "The 24th Hornbill Festival (Festival of Festivals) held at Kisama Heritage Village near Kohima, bringing together all 17 major indigenous tribes of Nagaland for traditional warrior dances, folk songs, bamboo games, and the Great Hornbill Rock concert.",
        "reference_keywords": ["hornbill festival", "kisama heritage village", "kohima nagaland", "naga tribes", "festival of festivals", "neiphiu rio", "northeast tourism"],
        "reference_hashtags": ["#HornbillFestival", "#Hornbill2023", "#KisamaHeritageVillage", "#NagalandTourism", "#FestivalOfFestivals", "#LandOfFestivals"],
        "key_entities": {
            "people": ["Neiphiu Rio", "Temjen Imna Along"],
            "organizations": ["Nagaland Tourism Department", "Nagaland Art and Culture Department"],
            "locations": ["Kisama", "Kohima", "Nagaland"],
            "demands": ["sustainable eco-tourism practices", "protection of tribal cultural intellectual property"]
        }
    }
]
