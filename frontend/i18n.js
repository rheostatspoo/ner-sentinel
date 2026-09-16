/*
 * i18n.js — small translation dictionary for multilingual notifications/UI,
 * as called for in the problem statement ("Support multilingual
 * notifications"). Covers the three most widely spoken languages across the
 * NER catchment area for this demo: English, Assamese, Hindi. Add more
 * languages (Khasi, Mizo, Manipuri, Nyishi...) by adding another key.
 */
const I18N = {
  en: {
    brandTag: "Landslide & slope-failure early warning — North Eastern Region",
    live: "LIVE",
    syncing: "syncing…",
    kpiZones: "Zones monitored",
    kpiAlerts: "Active alerts",
    kpiBlocked: "Roads blocked",
    kpiRestricted: "Roads restricted",
    kpiReports: "Field reports today",
    legendTitle: "Risk severity",
    tierLow: "Low", tierModerate: "Moderate", tierHigh: "High", tierSevere: "Severe",
    alertsTitle: "Early-warning feed",
    alertsSub: "Auto-generated from High & Severe zones",
    forecastTitle: "Weather-linked forecast",
    forecastSub: "48-hour rainfall outlook by zone",
    predictTitle: "Run the model",
    predictSub: "Test terrain & weather inputs against the Random Forest",
    fSlope: "Slope angle (°)", fElev: "Elevation (m)",
    fPrecip48: "Forecast rain, next 48h (mm)", fHistPrecip: "Rain, past 30 days (mm)",
    fEqCount: "Tremors, past 30d", fEqMag: "Max magnitude",
    fSoil: "Soil drainage group", fFault: "Distance to fault (km)",
    fNdvi: "Vegetation cover (NDVI)", fCalc: "Calculate risk",
    roadsTitle: "Road connectivity", roadsSub: "Status derived from the risk at each end point",
    priorityTitle: "Response prioritisation", prioritySub: "Ranked by risk × population exposure proxy",
    reportFab: "Report an incident",
    reportTitle: "Report a slope or road incident",
    rLat: "Latitude", rLon: "Longitude", useLocation: "Use my current location",
    rCategory: "What did you see?",
    catCrack: "Crack in ground or wall", catSlope: "Slope / soil movement",
    catRoad: "Road blocked or damaged", catFlood: "Flash flood", catOther: "Other",
    rDesc: "Description", rName: "Your name (optional)", rPhoto: "Photo or video still",
    rSubmit: "Submit report",
    rOfflineNote: "No signal? This still saves — it'll send the moment you're back online.",
    recentReports: "Recent field reports",
    loading: "Loading…",
    offlineMsg: "You're offline. Reports will sync automatically once connection returns.",
  },
  as: {
    brandTag: "নাহনি ধ্বংস আৰু ঢাল-বিপৰ্যয়ৰ পূৰ্ব সতৰ্কীকৰণ — উত্তৰ-পূৰ্বাঞ্চল",
    live: "প্ৰত্যক্ষ",
    syncing: "ছিংক হৈ আছে…",
    kpiZones: "নিৰীক্ষণাধীন অঞ্চল",
    kpiAlerts: "সক্ৰিয় সতৰ্কবাণী",
    kpiBlocked: "বন্ধ হোৱা ৰাস্তা",
    kpiRestricted: "সীমিত ৰাস্তা",
    kpiReports: "আজিৰ ফিল্ড ৰিপৰ্ট",
    legendTitle: "বিপদৰ মাত্ৰা",
    tierLow: "নিম্ন", tierModerate: "মধ্যম", tierHigh: "উচ্চ", tierSevere: "গুৰুতৰ",
    alertsTitle: "সতৰ্কীকৰণ ফীড",
    alertsSub: "উচ্চ আৰু গুৰুতৰ অঞ্চলৰ পৰা স্বয়ংক্ৰিয়ভাৱে সৃষ্টি",
    forecastTitle: "বতৰৰ পূৰ্বাভাস",
    forecastSub: "প্ৰতিটো অঞ্চলৰ ৪৮ ঘণ্টাৰ বৰষুণৰ পূৰ্বাভাস",
    predictTitle: "মডেল চলাওক",
    predictSub: "ভূখণ্ড আৰু বতৰৰ তথ্য পৰীক্ষা কৰক",
    fSlope: "ঢালৰ কোণ (°)", fElev: "উচ্চতা (মিটাৰ)",
    fPrecip48: "পূৰ্বাভাস বৰষুণ, ৪৮ ঘণ্টা (মিমি)", fHistPrecip: "যোৱা ৩০ দিনৰ বৰষুণ (মিমি)",
    fEqCount: "যোৱা ৩০ দিনৰ কম্পন", fEqMag: "সৰ্বোচ্চ মাত্ৰা",
    fSoil: "মাটিৰ নিষ্কাশন গোট", fFault: "চ্যুতিৰ পৰা দূৰত্ব (কিমি)",
    fNdvi: "উদ্ভিদ আচ্ছাদন (NDVI)", fCalc: "বিপদ গণনা কৰক",
    roadsTitle: "ৰাস্তা সংযোগ", roadsSub: "দুয়োপাৰৰ বিপদৰ ওপৰত ভিত্তি কৰি অৱস্থা",
    priorityTitle: "সঁহাৰি অগ্ৰাধিকাৰ", prioritySub: "বিপদ × জনসংখ্যাৰ ভিত্তিত ক্ৰমাংক",
    reportFab: "ঘটনা ৰিপৰ্ট কৰক",
    reportTitle: "ঢাল বা ৰাস্তাৰ ঘটনা ৰিপৰ্ট কৰক",
    rLat: "অক্ষাংশ", rLon: "দ্ৰাঘিমাংশ", useLocation: "মোৰ বৰ্তমান অৱস্থান ব্যৱহাৰ কৰক",
    rCategory: "আপুনি কি দেখিলে?",
    catCrack: "মাটি বা দেৱালত ফাট", catSlope: "ঢাল/মাটি স্থানান্তৰ",
    catRoad: "ৰাস্তা বন্ধ বা ক্ষতিগ্ৰস্ত", catFlood: "আকস্মিক বান", catOther: "আন",
    rDesc: "বিৱৰণ", rName: "আপোনাৰ নাম (ঐচ্ছিক)", rPhoto: "ফটো বা ভিডিঅ' ছবি",
    rSubmit: "ৰিপৰ্ট দাখিল কৰক",
    rOfflineNote: "সংযোগ নাই? এইটো তথাপি ছেভ হ'ব — সংযোগ ঘূৰাই পালে পঠিওৱা হ'ব।",
    recentReports: "শেহতীয়া ফিল্ড ৰিপৰ্ট",
    loading: "লোড হৈ আছে…",
    offlineMsg: "আপুনি অফলাইনত আছে। সংযোগ ঘূৰাই আহিলে ৰিপৰ্ট স্বয়ংক্ৰিয়ভাৱে পঠিওৱা হ'ব।",
  },
  hi: {
    brandTag: "भूस्खलन एवं ढलान-विफलता पूर्व चेतावनी — पूर्वोत्तर क्षेत्र",
    live: "लाइव",
    syncing: "सिंक हो रहा है…",
    kpiZones: "निगरानी क्षेत्र",
    kpiAlerts: "सक्रिय अलर्ट",
    kpiBlocked: "अवरुद्ध सड़कें",
    kpiRestricted: "प्रतिबंधित सड़कें",
    kpiReports: "आज की फील्ड रिपोर्ट",
    legendTitle: "जोखिम स्तर",
    tierLow: "कम", tierModerate: "मध्यम", tierHigh: "उच्च", tierSevere: "गंभीर",
    alertsTitle: "पूर्व-चेतावनी फ़ीड",
    alertsSub: "उच्च व गंभीर क्षेत्रों से स्वतः तैयार",
    forecastTitle: "मौसम-आधारित पूर्वानुमान",
    forecastSub: "प्रत्येक क्षेत्र के लिए 48 घंटे का वर्षा पूर्वानुमान",
    predictTitle: "मॉडल चलाएँ",
    predictSub: "इलाके व मौसम इनपुट को रैंडम फ़ॉरेस्ट पर परखें",
    fSlope: "ढलान कोण (°)", fElev: "ऊँचाई (मीटर)",
    fPrecip48: "पूर्वानुमानित वर्षा, अगले 48 घंटे (मिमी)", fHistPrecip: "पिछले 30 दिनों की वर्षा (मिमी)",
    fEqCount: "पिछले 30 दिनों के भूकंपीय झटके", fEqMag: "अधिकतम तीव्रता",
    fSoil: "मृदा जल-निकासी वर्ग", fFault: "भ्रंश रेखा से दूरी (किमी)",
    fNdvi: "वनस्पति आवरण (NDVI)", fCalc: "जोखिम गणना करें",
    roadsTitle: "सड़क संपर्क", roadsSub: "दोनों छोर के जोखिम से निर्धारित स्थिति",
    priorityTitle: "प्रतिक्रिया प्राथमिकता", prioritySub: "जोखिम × जनसंख्या के आधार पर क्रम",
    reportFab: "घटना दर्ज करें",
    reportTitle: "ढलान या सड़क की घटना दर्ज करें",
    rLat: "अक्षांश", rLon: "देशांतर", useLocation: "मेरा वर्तमान स्थान उपयोग करें",
    rCategory: "आपने क्या देखा?",
    catCrack: "ज़मीन या दीवार में दरार", catSlope: "ढलान/मिट्टी खिसकना",
    catRoad: "सड़क अवरुद्ध या क्षतिग्रस्त", catFlood: "अचानक बाढ़", catOther: "अन्य",
    rDesc: "विवरण", rName: "आपका नाम (वैकल्पिक)", rPhoto: "फ़ोटो या वीडियो स्थिर छवि",
    rSubmit: "रिपोर्ट भेजें",
    rOfflineNote: "नेटवर्क नहीं है? यह फिर भी सेव होगा — कनेक्शन वापस आते ही भेज दिया जाएगा।",
    recentReports: "हाल की फील्ड रिपोर्ट",
    loading: "लोड हो रहा है…",
    offlineMsg: "आप ऑफ़लाइन हैं। कनेक्शन वापस आते ही रिपोर्ट अपने-आप भेज दी जाएँगी।",
  },
};

let currentLang = "en";

function applyI18n(lang) {
  currentLang = lang;
  const dict = I18N[lang] || I18N.en;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
  document.documentElement.lang = lang;
}

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || I18N.en[key] || key;
}
