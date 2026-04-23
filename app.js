// ============================================================
// RADIANCE v6 — Hip home protocol + per-set tracker + badges
// ============================================================
const APP_VERSION = 6;

// ---------- EXERCISES ----------
const EX = {
  // --- CARDIO (reference only; workouts use type:'cardio' machine-picker blocks) ---
  bike:{name:'Stationary Bike',cat:'cardio',primary:['Legs','Heart'],secondary:['Glutes'],equip:'Upright or recumbent bike',yt:'https://www.youtube.com/results?search_query=female+stationary+bike+beginner+form',form:['Seat height: slight knee bend at bottom of stroke','Sit tall, shoulders relaxed','Gentle on hips and knees','Great choice on days things feel sore']},
  stair:{name:'Stair Stepper',cat:'cardio',primary:['Glutes','Quads','Calves'],secondary:['Core'],equip:'StairMaster or similar',yt:'https://www.youtube.com/results?search_query=female+stair+stepper+workout+form',form:['Stand tall, light fingertip touch on rails','Full steps — don\'t short-step','Press through whole foot, not just toes','Breathe through the challenge']},
  tread_walk:{name:'Treadmill Walk (Incline)',cat:'cardio',primary:['Glutes','Hamstrings'],secondary:['Calves','Core'],equip:'Treadmill',yt:'https://www.youtube.com/results?search_query=female+incline+treadmill+walking+workout',form:['Speed 3.0–3.5 mph (brisk walk)','ALWAYS interval the incline — never hold max','Alternate 2 min high / 2 min flat','Light rail touch for balance only, don\'t hang on']},
  tread_run:{name:'Treadmill Jog',cat:'cardio',primary:['Legs','Heart'],secondary:['Core'],equip:'Treadmill',yt:'https://www.youtube.com/results?search_query=female+beginner+treadmill+running',form:['Only if you\'re feeling it — never required','Soft landings, midfoot','Arms relaxed at 90°','Walk breaks anytime']},
  rower:{name:'Rowing Machine',cat:'cardio',primary:['Back','Legs','Core'],secondary:['Arms','Heart'],equip:'Concept 2 or similar',yt:'https://www.youtube.com/results?search_query=female+rowing+machine+beginner+form',form:['Drive: LEGS first, then lean back, then arms','Return: arms, lean, bend knees','80% legs, 20% arms','Excellent full-body — easy on joints']},
  elliptical:{name:'Elliptical',cat:'cardio',primary:['Legs','Heart'],secondary:['Glutes','Arms'],equip:'Elliptical',yt:'https://www.youtube.com/results?search_query=female+elliptical+workout+beginner',form:['Stand tall, push and pull with arms','Try forward AND backward — backward hits glutes','Low impact, happy hips','Good for anyone feeling sore']},

  // --- HIP HOME PROTOCOL (from user\'s trainer) ---
  sl_rdl:{name:'Single-Leg RDL',cat:'hip_home',primary:['Glutes','Hamstrings'],secondary:['Core','Balance'],equip:'Dumbbell',unit:'total',defaultBase:15,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+single+leg+romanian+deadlift+form',
    form:[
      'Stand on one leg, slight bend in standing knee',
      'Hold DB in opposite hand (or both hands light to start)',
      'Hinge at the hip — extend free leg straight back as torso tips forward',
      'Keep hips square (don\'t let the back hip rotate up)',
      'Back leg, torso, and head form one straight line',
      'Drive through standing heel to stand, squeeze glute at top',
      'Switch legs every set — 8 each side'
    ]},
  warrior_raise:{name:'Warrior-III Balance Raise',cat:'hip_home',primary:['Glutes','Core','Shoulders'],secondary:['Hip Stabilizers'],equip:'Light DB(s)',unit:'each',defaultBase:3,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+warrior+3+front+raise+balance',
    form:[
      'Stand on one leg, very light DB(s) in hands',
      'Simultaneously raise arms straight forward to shoulder height AND opposite leg straight back',
      'End position: arms, torso, raised leg all parallel to floor',
      'Hold 1–2 seconds at the top',
      'Return with control',
      '8 each leg — balance is the point, not speed'
    ]},
  seated_band_abd:{name:'Seated Band Abduction',cat:'hip_home',primary:['Glute Medius'],secondary:['Hip Stabilizers'],equip:'Mini band above knees',unit:'total',defaultBase:0,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+seated+banded+hip+abduction+glute+medius',
    form:[
      'Sit tall, mini band above both knees',
      'Feet flat, knees at 90°',
      'Round 1: right knee out 10× (slow, squeeze), pause',
      'Round 2: left knee out 10×, pause',
      'Round 3: both knees out together 10×',
      'Burn on SIDE of hip = glute medius working',
      'One \"set\" = all three rounds'
    ]},
  db_calf_raise:{name:'Dumbbell Calf Raise',cat:'hip_home',primary:['Calves'],secondary:['Ankle Stability'],equip:'Dumbbells',unit:'each',defaultBase:20,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+dumbbell+standing+calf+raise',
    form:[
      'Stand tall, DB in each hand at sides',
      'Rise onto balls of feet as high as possible',
      'Pause 1 second at the top',
      'Lower slowly until heels just touch',
      'Optional: stand on a plate or step for more range'
    ]},

  // --- TONE (GYM STRENGTH) ---
  trap_dl:{name:'Trap Bar Deadlift',cat:'tone',primary:['Glutes','Hamstrings','Quads'],secondary:['Back','Core'],equip:'Trap bar',unit:'total',defaultBase:65,rest:75,
    yt:'https://www.youtube.com/results?search_query=female+trap+bar+deadlift+form',
    form:['Stand centered in bar, feet hip-width','Hinge at hips, grip high handles','Flat back, chest up','Big breath, brace core','Drive through whole foot to stand','Squeeze glutes at top']},
  goblet:{name:'Goblet Squat',cat:'tone',primary:['Glutes','Quads'],secondary:['Core'],equip:'Dumbbell',unit:'total',defaultBase:20,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+goblet+squat+form',
    form:['Hold DB at chest with both hands','Feet shoulder-width, toes slightly out','Sit back and down — only as deep as comfortable','Drive through whole foot to stand','Squeeze glutes at top']},
  db_lunge:{name:'Reverse Lunge',cat:'tone',primary:['Glutes','Quads'],secondary:['Hamstrings','Core'],equip:'Dumbbells',unit:'each',defaultBase:10,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+reverse+lunge+dumbbell+form',
    form:['Step BACKWARD (easier on knees than forward)','Lower until both knees ~90°','Push through front heel to stand','Bodyweight fine to start']},
  hip_thrust:{name:'Hip Thrust',cat:'tone',primary:['Glutes'],secondary:['Hamstrings','Core'],equip:'Dumbbell + bench',unit:'total',defaultBase:25,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+dumbbell+hip+thrust+glutes',
    form:['Upper back on bench, feet flat','DB across hips (pad it)','Drive hips up, squeeze glutes HARD','Pause 2 seconds at top','Best glute exercise there is']},
  db_bench:{name:'Dumbbell Bench Press',cat:'tone',primary:['Chest'],secondary:['Shoulders','Triceps'],equip:'Dumbbells + flat bench',unit:'each',defaultBase:12,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+dumbbell+bench+press+form',
    form:['Lie flat, feet on floor','Shoulder blades pinched','DBs at chest, press up','Lower slowly, feel the stretch','Don\'t lock out']},
  db_row:{name:'Dumbbell Row',cat:'tone',primary:['Back','Lats'],secondary:['Biceps','Rear Delts'],equip:'Dumbbell + bench',unit:'each',defaultBase:15,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+one+arm+dumbbell+row+form',
    form:['One hand and knee on bench, other foot wide','Pull DB to hip — elbow to ceiling','Squeeze shoulder blade at top','Lower with full stretch','Builds a strong, toned back']},
  db_shoulder:{name:'Seated Shoulder Press',cat:'tone',primary:['Shoulders'],secondary:['Triceps'],equip:'Dumbbells + upright bench',unit:'each',defaultBase:10,rest:60,
    yt:'https://www.youtube.com/results?search_query=female+seated+dumbbell+shoulder+press',
    form:['Seated, bench at 90°','DBs at shoulders, palms forward','Press straight up','Lower to shoulders','Brace core — don\'t arch back']},
  pushup:{name:'Push-Up',cat:'tone',primary:['Chest','Shoulders'],secondary:['Triceps','Core'],equip:'Bodyweight',unit:'total',defaultBase:0,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+push+up+modified+beginner',
    form:['From knees or toes — both are great','Hands slightly wider than shoulders','Lower chest toward floor, push up','Modified is smart, not easy']},
  db_curl:{name:'Bicep Curl',cat:'tone',primary:['Biceps'],secondary:['Forearms'],equip:'Dumbbells',unit:'each',defaultBase:8,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+dumbbell+bicep+curl+form',
    form:['DBs at sides, palms forward','Curl up, elbows pinned to sides','Squeeze at top','Lower slowly — fight the weight down']},
  tri_kick:{name:'Tricep Kickback',cat:'tone',primary:['Triceps'],secondary:[],equip:'Dumbbells',unit:'each',defaultBase:5,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+tricep+kickback+form',
    form:['Hinge forward at hips, flat back','Upper arms against your sides, elbows bent 90°','Extend arms straight back','Squeeze tricep hard','Tones back of the arm']},
  lat_raise:{name:'Lateral Raise',cat:'tone',primary:['Side Delts'],secondary:['Traps'],equip:'Dumbbells',unit:'each',defaultBase:5,rest:45,
    yt:'https://www.youtube.com/results?search_query=female+lateral+raise+dumbbell+form',
    form:['Light DBs at sides','Raise arms to sides until parallel to floor','Slight elbow bend throughout','Shapes the shoulders — use lighter than you think']},

  // --- CORE ---
  plank:{name:'Plank',cat:'core',primary:['Core'],secondary:['Glutes','Shoulders'],equip:'Bodyweight',time:45,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+plank+form+beginner',
    form:['Forearms on floor, straight line head to heels','Squeeze glutes and brace core','From knees is totally valid','Breathe the whole time']},
  dead_bug:{name:'Dead Bug',cat:'core',primary:['Core'],secondary:['Hip Flexors'],equip:'Bodyweight',unit:'total',defaultBase:0,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+dead+bug+core+exercise',
    form:['On back, arms up, knees bent 90°','Extend opposite arm and leg slowly','Keep lower back PRESSED to floor','Return with control']},
  bird_dog:{name:'Bird Dog',cat:'core',primary:['Core','Glutes'],secondary:['Shoulders'],equip:'Bodyweight',unit:'total',defaultBase:0,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+bird+dog+core+exercise',
    form:['Hands and knees, neutral spine','Extend opposite arm and leg','Hold 1–2 seconds','Keep hips level — don\'t sway']},
  side_plank:{name:'Side Plank',cat:'core',primary:['Obliques','Hip Stabilizers'],secondary:[],equip:'Bodyweight',time:25,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+side+plank+form',
    form:['On side, forearm on floor','Lift hips high, straight line','From knees is great','Strong side-hip builder']},
  bike_crunch:{name:'Bicycle Crunch',cat:'core',primary:['Obliques','Abs'],secondary:[],equip:'Bodyweight',unit:'total',defaultBase:0,rest:30,
    yt:'https://www.youtube.com/results?search_query=female+bicycle+crunch+form',
    form:['On back, hands behind head (light touch)','Opposite elbow to knee','Slow and controlled — no yanking neck','Feel the twist']}
};

// ---------- MASSAGE GUN PROTOCOL ----------
// Shown as its own pre-workout block, not a set-tracked exercise.
const MASSAGE = [
  {name:'Glute Maximus',time:'30 sec each side',note:'Large back-of-hip muscle.'},
  {name:'Glute Medius',time:'30 sec each side',note:'Side of hip — between the top of the pelvis and the hip joint.'},
  {name:'Inner Thigh / Adductors',time:'30 sec each side',note:'Tight adductors pull on the hip and mimic hip pain. Don\'t skip these.'}
];

// Hip home block used by scoped phases (helper returns the array).
function hipHomeBlock(){
  return [
    {section:'Home Routine · Before Gym'},
    {type:'massage'},
    {id:'sl_rdl',sets:3,reps:8,each:true,rest:45},
    {id:'warrior_raise',sets:3,reps:8,each:true,rest:45},
    {id:'seated_band_abd',sets:3,reps:10,rest:30,note:'1 round = R 10x, L 10x, both 10x. 3 rounds.'},
    {id:'db_calf_raise',sets:3,reps:15,rest:30}
  ];
}

// ---------- PHASES ----------
const PHASES = [
  {id:1,name:'Spark',tag:'Your beautiful beginning',weeks:4,cardioDays:3,toneDays:1,
    desc:'Four days a week. Three cardio days, one strength day. Hip home routine every workout day — the work that actually fixes the hip.',
    prog:'Cardio: 25–30 min steady. Strength: light, 3×10–12. Hip home routine: every session.',
    schedule:[{type:'cardio',wk:'cardio_ss'},{type:'tone',wk:'tone_a'},{type:'rest'},{type:'cardio',wk:'cardio_ss'},{type:'cardio',wk:'cardio_mix'},{type:'rest'},{type:'rest'}],
    workouts:{
      cardio_ss:{name:'Steady Cardio',focus:'Your Choice · Machine',dur:'30 min',exercises:[
        {section:'Warm-Up'},{type:'cardio',duration:5,pattern:'easy',note:'Easy pace, get moving.'},
        {section:'Main'},{type:'cardio',duration:25,pattern:'steady',note:'Steady RPE 5 — you can talk the whole time.'}
      ]},
      cardio_mix:{name:'Two Machines',focus:'Variety',dur:'35 min',exercises:[
        {section:'Machine 1'},{type:'cardio',duration:20,pattern:'steady',note:'Pick one machine, steady pace.'},
        {section:'Machine 2'},{type:'cardio',duration:15,pattern:'easy',note:'Switch machines. Easier finish.'}
      ]},
      tone_a:{name:'Full Body Strength',focus:'Gym',dur:'40 min',exercises:[
        {section:'Strength'},
        {id:'goblet',sets:3,reps:12,rest:60,note:'Light. Depth over weight.'},
        {id:'hip_thrust',sets:3,reps:12,rest:60,note:'Squeeze glutes 2 seconds at top.'},
        {id:'db_bench',sets:3,reps:10,rest:60,note:'Light DBs to learn the groove.'},
        {id:'db_row',sets:3,reps:10,each:true,rest:60,note:'Pull to hip. Each arm.'},
        {id:'db_shoulder',sets:3,reps:10,rest:60,note:'Seated. Controlled.'},
        {section:'Core'},
        {id:'plank',sets:3,time:30,rest:30,note:'From knees fine.'}
      ]}
    }
  },
  {id:2,name:'Kindle',tag:'Fanning the flame',weeks:4,cardioDays:3,toneDays:1,
    desc:'Same 4 days. Cardio sessions stretch a little longer. Still doing the home routine every workout day.',
    prog:'Cardio: 30–35 min. Strength: slightly heavier if last time felt easy.',
    schedule:[{type:'cardio',wk:'cardio_ss_30'},{type:'tone',wk:'tone_b'},{type:'rest'},{type:'cardio',wk:'cardio_incline'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'},{type:'rest'}],
    workouts:{
      cardio_ss_30:{name:'Steady Cardio',focus:'Your Choice · Machine',dur:'35 min',exercises:[
        {section:'Warm-Up'},{type:'cardio',duration:5,pattern:'easy',note:'Easy.'},
        {section:'Main'},{type:'cardio',duration:30,pattern:'steady',note:'Steady RPE 5–6. Switch machine at 15 min if you want.'}
      ]},
      cardio_incline:{name:'Incline Walk',focus:'Treadmill · Interval Incline',dur:'35 min',exercises:[
        {section:'Warm-Up'},{type:'cardio',duration:5,pattern:'easy',note:'Flat, easy.'},
        {section:'Main'},{type:'cardio',duration:25,pattern:'incline_intervals',note:'3.0 mph: 2 min at 6% / 2 min at 2% — ALWAYS interval the incline (prevents shin pain).'},
        {section:'Cool Down'},{type:'cardio',duration:5,pattern:'easy',note:'Easy walk.'}
      ]},
      cardio_mix_35:{name:'Two Machines',focus:'Variety',dur:'40 min',exercises:[
        {section:'Machine 1'},{type:'cardio',duration:20,pattern:'steady',note:'Steady.'},
        {section:'Machine 2'},{type:'cardio',duration:15,pattern:'steady',note:'Different machine.'}
      ]},
      tone_b:{name:'Full Body Strength',focus:'Gym',dur:'40 min',exercises:[
        {section:'Strength'},
        {id:'trap_dl',sets:3,reps:10,rest:75,note:'The king of hip hinges. Flat back, drive through feet.'},
        {id:'goblet',sets:3,reps:12,rest:60,note:'Heavier if last time felt easy.'},
        {id:'hip_thrust',sets:3,reps:15,rest:60,note:'Squeeze every rep.'},
        {id:'db_row',sets:3,reps:10,each:true,rest:60,note:'Strong back.'},
        {id:'db_shoulder',sets:3,reps:10,rest:60,note:'Shoulders.'},
        {id:'lat_raise',sets:2,reps:12,each:true,rest:45,note:'Shapes the shoulders.'},
        {section:'Core'},
        {id:'bird_dog',sets:3,reps:10,each:true,rest:30,note:'Balance + core.'},
        {id:'side_plank',sets:2,time:25,rest:30,each:true,note:'Each side. From knees fine.'}
      ]}
    }
  },
  {id:3,name:'Ignite',tag:'Adding a spark',weeks:4,cardioDays:3,toneDays:1,
    desc:'Last phase of intensive hip work. Home routine every workout day. Cardio picks up a little.',
    prog:'Cardio: 35 min, a touch of interval work at the end.',
    schedule:[{type:'cardio',wk:'cardio_intervals'},{type:'tone',wk:'tone_upper'},{type:'rest'},{type:'cardio',wk:'cardio_ss_30'},{type:'cardio',wk:'cardio_circuit'},{type:'rest'},{type:'rest'}],
    workouts:{
      cardio_intervals:{name:'Mostly Steady + Intervals',focus:'Your Choice',dur:'35 min',exercises:[
        {section:'Warm-Up'},{type:'cardio',duration:5,pattern:'easy',note:'Easy start.'},
        {section:'Steady'},{type:'cardio',duration:22,pattern:'steady',note:'Steady RPE 5–6.'},
        {section:'Intervals'},{type:'cardio',duration:8,pattern:'intervals_1_1',note:'1 min harder / 1 min easy. \"Harder\" = brisk, not dying.'}
      ]},
      cardio_circuit:{name:'3-Machine Circuit',focus:'Variety',dur:'40 min',exercises:[
        {section:'Machine 1 · 12 min'},{type:'cardio',duration:12,pattern:'steady',note:'Pick one — steady.'},
        {section:'Machine 2 · 12 min'},{type:'cardio',duration:12,pattern:'steady',note:'Switch. Different muscles.'},
        {section:'Machine 3 · 12 min'},{type:'cardio',duration:12,pattern:'easy',note:'Switch again. Cool down on this one.'}
      ]},
      tone_upper:{name:'Upper Body + Core',focus:'Gym',dur:'40 min',exercises:[
        {section:'Upper Body'},
        {id:'db_bench',sets:3,reps:10,rest:60,note:'Chest.'},
        {id:'db_row',sets:3,reps:10,each:true,rest:60,note:'Back.'},
        {id:'db_shoulder',sets:3,reps:10,rest:60,note:'Shoulders.'},
        {id:'pushup',sets:3,reps:10,rest:45,note:'Modified or toes — both great.'},
        {id:'lat_raise',sets:3,reps:12,each:true,rest:45,note:'Shoulder shape.'},
        {id:'db_curl',sets:2,reps:12,each:true,rest:45,note:'Arms.'},
        {id:'tri_kick',sets:2,reps:12,each:true,rest:45,note:'Back of arms.'},
        {section:'Core'},
        {id:'plank',sets:3,time:45,rest:30,note:'Longer hold.'},
        {id:'dead_bug',sets:3,reps:10,each:true,rest:30,note:'Press low back to floor.'}
      ]}
    }
  },
  {id:4,name:'Energize',tag:'Feeling the change',weeks:4,cardioDays:4,toneDays:1,
    desc:'Cardio steps up to 4 days. Home routine drops to once a week — a check-in. If your hip feels good, trust it.',
    prog:'Cardio: 35 min, more intervals. Home routine: once a week.',
    schedule:[{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_circuit'},{type:'tone',wk:'tone_upper'},{type:'rest'},{type:'cardio',wk:'cardio_ss_30'},{type:'cardio',wk:'cardio_row'},{type:'rest'}],
    workouts:{
      cardio_intervals_35:{name:'Cardio + Intervals',focus:'Your Choice',dur:'40 min',exercises:[
        {section:'Warm-Up'},{type:'cardio',duration:5,pattern:'easy',note:'Easy.'},
        {section:'Steady'},{type:'cardio',duration:22,pattern:'steady',note:'Steady RPE 5–6.'},
        {section:'Intervals'},{type:'cardio',duration:13,pattern:'intervals_1_1',note:'1 min harder / 1 min easy. Should feel challenging, not max.'}
      ]},
      cardio_row:{name:'Row + Easy',focus:'Rower + Bike/Elliptical',dur:'40 min',exercises:[
        {section:'Rower'},{type:'cardio',duration:20,pattern:'steady',fixed:'rower',note:'Drive with legs first. If you haven\'t rowed, today is the day.'},
        {section:'Finish'},{type:'cardio',duration:20,pattern:'easy',note:'Any other machine, easy pace.'}
      ]}
    }
  },
  {id:5,name:'Rise',tag:'Watch yourself rise',weeks:4,cardioDays:4,toneDays:1,
    desc:'Home routine is optional now — available in the Program tab any time. If your hip is happy, celebrate it. If it flares, the routine is one tap away.',
    prog:'Cardio: 35–40 min. Rower features.',
    schedule:[{type:'cardio',wk:'cardio_circuit'},{type:'cardio',wk:'cardio_row'},{type:'tone',wk:'tone_lower'},{type:'rest'},{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'}],
    workouts:{
      tone_lower:{name:'Lower Body',focus:'Gym',dur:'40 min',exercises:[
        {section:'Lower Body'},
        {id:'goblet',sets:3,reps:12,rest:60,note:'Depth over weight.'},
        {id:'hip_thrust',sets:3,reps:15,rest:60,note:'Squeeze every rep.'},
        {id:'db_lunge',sets:3,reps:10,each:true,rest:60,note:'Reverse lunges.'},
        {id:'trap_dl',sets:3,reps:10,rest:75,note:'Hinge. Flat back.'},
        {section:'Core'},
        {id:'plank',sets:3,time:45,rest:30},
        {id:'bike_crunch',sets:3,reps:10,each:true,rest:30,note:'Slow, controlled.'}
      ]}
    }
  },
  {id:6,name:'Empower',tag:'Own your strength',weeks:4,cardioDays:4,toneDays:1,
    desc:'Peak of the 5-day block. You\'re strong, confident, moving differently. This is empowerment.',
    prog:'Cardio: 40 min, 10–12 min intervals.',
    schedule:[{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_ss_30'},{type:'tone',wk:'tone_upper'},{type:'rest'},{type:'cardio',wk:'cardio_row'},{type:'cardio',wk:'cardio_circuit'},{type:'rest'}],workouts:{}
  },
  {id:7,name:'Transform',tag:'Becoming',weeks:4,cardioDays:4,toneDays:1,
    desc:'The groove is deep. Five days a week feels normal now.',
    prog:'5 days — 4 cardio + 1 tone. Cardio: 40 min.',
    schedule:[{type:'cardio',wk:'cardio_row'},{type:'cardio',wk:'cardio_intervals_35'},{type:'tone',wk:'tone_lower'},{type:'rest'},{type:'cardio',wk:'cardio_circuit'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'}],workouts:{}
  },
  {id:8,name:'Elevate',tag:'Rising higher',weeks:4,cardioDays:4,toneDays:1,
    desc:'You don\'t recognize old photos. The mirror shows someone strong and radiant.',
    prog:'5 days. Peak cardio volume. 40–45 min sessions.',
    schedule:[{type:'cardio',wk:'cardio_circuit'},{type:'cardio',wk:'cardio_ss_30'},{type:'tone',wk:'tone_upper'},{type:'rest'},{type:'cardio',wk:'cardio_row'},{type:'cardio',wk:'cardio_intervals_35'},{type:'rest'}],workouts:{}
  },
  {id:9,name:'Shine',tag:'Let the world see',weeks:4,cardioDays:4,toneDays:1,
    desc:'You shine — stronger, more alive. Variety peaks. The body adapts to nothing because we change everything.',
    prog:'5 days. Maximum variety across machines and patterns.',
    schedule:[{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_row'},{type:'tone',wk:'tone_lower'},{type:'rest'},{type:'cardio',wk:'cardio_circuit'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'}],workouts:{}
  },
  {id:10,name:'Glow',tag:'You\'re glowing',weeks:4,cardioDays:4,toneDays:2,
    desc:'Six days now. Four cardio, two strength. This is your peak.',
    prog:'6 days. 4 cardio + 2 tone.',
    schedule:[{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_row'},{type:'cardio',wk:'cardio_circuit'},{type:'tone',wk:'tone_upper'},{type:'cardio',wk:'cardio_ss_30'},{type:'tone',wk:'tone_lower'},{type:'rest'}],workouts:{}
  },
  {id:11,name:'Flourish',tag:'Thriving beautifully',weeks:4,cardioDays:5,toneDays:1,
    desc:'You are flourishing — strong body, clear mind. This is who you’ve always been.',
    prog:'6 days. Cardio you love, strength that keeps you toned.',
    schedule:[{type:'cardio',wk:'cardio_circuit'},{type:'cardio',wk:'cardio_ss_30'},{type:'cardio',wk:'cardio_row'},{type:'tone',wk:'tone_upper'},{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'}],workouts:{}
  },
  {id:12,name:'Radiance',tag:'This is you',weeks:4,cardioDays:5,toneDays:1,
    desc:'Not an ending — a beginning. You’ve built habits that last forever. You are radiant.',
    prog:'6 glorious days. Sustainable peak. You never have to go back.',
    schedule:[{type:'cardio',wk:'cardio_row'},{type:'cardio',wk:'cardio_intervals_35'},{type:'cardio',wk:'cardio_circuit'},{type:'tone',wk:'tone_upper'},{type:'cardio',wk:'cardio_ss_30'},{type:'cardio',wk:'cardio_mix_35'},{type:'rest'}],workouts:{}
  }
];
(function(){ var w=1; PHASES.forEach(function(p){ p.startWeek=w; w+=p.weeks; }); })();

// ---------- CARDIO PATTERNS ----------
const CARDIO_PATTERNS = {
  easy:'Easy pace — you could sing.',
  steady:'Steady RPE 5–6 — you can talk but not sing.',
  incline_intervals:'Treadmill 3.0 mph: 2 min high incline / 2 min low incline. Never sustain max.',
  intervals_1_1:'1 min harder / 1 min easy, repeat. “Harder” = brisk, not max.',
  intervals_2_1:'2 min moderate / 1 min hard, repeat. Finish on easy.'
};
const MACHINES = [
  {id:'bike',label:'Bike',emoji:'🚴‍♀️',cue:'Resistance 5–7, steady cadence. Gentle on hips.'},
  {id:'stair',label:'Stair',emoji:'👣',cue:'Full steps. Light fingertip touch — don’t hang on rails.'},
  {id:'tread_walk',label:'Incline Walk',emoji:'🚶‍♀️',cue:'3.0–3.5 mph. INTERVAL the incline — never max sustained.'},
  {id:'tread_run',label:'Jog',emoji:'🏃‍♀️',cue:'Only if you feel it. Soft midfoot landing.'},
  {id:'rower',label:'Rower',emoji:'🚣‍♀️',cue:'Legs first, then lean, then arms. 80% legs.'},
  {id:'elliptical',label:'Elliptical',emoji:'✨',cue:'Try forward AND backward. Backward hits glutes more.'}
];

// ---------- NUTRITION (unchanged) ----------
var NOURISH = {
  dayFocus:{cardio:'Hydrate before and after. Include protein with your next meal — muscles need it.',tone:'Protein helps muscles recover and stay toned. Make it the star of your plate today.',rest:'Rest days are when your body gets stronger. Nourish with colorful, protein-rich foods.'},
  meals:[
    {name:'Breakfast Ideas',note:'Start with protein. It keeps you satisfied and energized all day.',ex:['Greek yogurt parfait with berries and granola','Veggie egg white omelette with spinach','Protein smoothie: spinach, banana, protein powder, almond milk','2 eggs + slice of whole grain toast','Overnight oats with chia seeds and berries']},
    {name:'Lunch Ideas',note:'Protein first, then veggies, then a small grain.',ex:['Grilled chicken salad with colorful veggies','Turkey lettuce wraps with avocado','Lentil soup with a side salad','Tuna salad on whole grain bread','Chicken veggie stir fry over rice']},
    {name:'Dinner Ideas',note:'Satisfied, not stuffed. Protein + veggies is the formula.',ex:['Baked salmon with roasted vegetables','Lean ground turkey stir fry','Chicken breast with sweet potato and broccoli','Shrimp with zucchini noodles','Turkey meatballs with spaghetti squash']}
  ],
  snacks:[{old:'Chips',better:'Roasted chickpeas or hummus + veggies'},{old:'Crackers',better:'Rice cakes with almond butter'},{old:'Candy',better:'Frozen grapes or dark chocolate square'},{old:'Ice cream',better:'Frozen Greek yogurt bark'},{old:'Cookies',better:'Protein bites or protein bar'},{old:'Granola bar',better:'String cheese + almonds'},{old:'Sugary cereal',better:'Greek yogurt + berries + honey'},{old:'Soda',better:'Sparkling water with lemon'}],
  wellness:['Your body thrives on protein — include some with every meal and snack','Small, satisfying portions work beautifully. Listen to your body.','Staying hydrated helps you feel amazing — water bottle always','Colorful plates are happy plates — 2–3 colors per meal','Ginger or peppermint tea are wonderful for settling your stomach','Every meal is a chance to nourish yourself — no guilt, just fuel for your glow','Protein keeps you satisfied between meals','Eating slowly helps you feel satisfied','Sleep is magic — 7–8 hours helps everything'],
  hydration:['Aim for a water bottle with every meal — more on workout days','Keep a pretty water bottle visible always','Infused water: cucumber+mint, lemon+ginger, strawberry+basil','Herbal tea counts! Chamomile, peppermint, ginger','Full glass first thing every morning','Sparkling water is wonderful if plain is boring']
};

// ---------- BADGES ----------
const COUNT_BADGES = [
  {id:'first_bloom',n:1,icon:'🌱',name:'First Bloom',msg:'You showed up. That is the whole secret.'},
  {id:'rooted',n:7,icon:'🌸',name:'Rooted',msg:'Seven sessions — you have roots now.'},
  {id:'blooming',n:14,icon:'🌺',name:'Blooming',msg:'Fourteen! The transformation is beginning to show.'},
  {id:'flourishing',n:30,icon:'🌷',name:'Flourishing',msg:'Thirty workouts. You are flourishing beautifully.'},
  {id:'in_full_radiance',n:60,icon:'🌹',name:'In Full Radiance',msg:'Sixty. This is who you are now.'},
  {id:'crowned',n:100,icon:'👑',name:'Crowned',msg:'One hundred workouts. You earned your crown.'},
  {id:'luminous',n:150,icon:'✨',name:'Luminous',msg:'You are lit from within.'},
  {id:'diamond_heart',n:200,icon:'💎',name:'Diamond Heart',msg:'Two hundred. Unbreakable.'}
];

const CELEBRATIONS = [
  'You showed up. That’s everything.',
  'Another petal in full bloom.',
  'Radiance earned.',
  'Strong body, stronger mind.',
  'You did it — again.',
  'That’s another one for future you.',
  'Beautiful work today.',
  'You chose yourself.',
  'Another brick in something strong.',
  'Your glow is earned.',
  'Proud of you. Keep going.',
  'One more session your future self will thank you for.',
  'Today counts. All of them count.',
  'Strong is the new pretty — you are both.',
  'Showed up tired? Even better.',
  'The hard ones count the most.',
  'Your consistency is changing everything.',
  'Look at you go.',
  'You are writing a quiet, powerful story.',
  'That was a gift to yourself.',
  'Another petal. Another bloom.',
  'Radiance is a verb, and you just did it.',
  'You earned every ounce of how you’ll feel tomorrow.',
  'Not every day has to be perfect. Today was enough.',
  'You are the kind of woman who shows up. Never forget that.'
];

const AFFIRMATIONS = [
  'My body is strong, capable, and worthy of care.',
  'I am the kind of woman who shows up for herself.',
  'Every session is an act of love.',
  'I am becoming — and that is enough.',
  'My strength is not loud. It is steady.',
  'Small, consistent acts are changing my life.',
  'My worth is not a number. It is a way of being.',
  'I trust my body. It is doing beautiful work.',
  'Rest is part of the progress, not a break from it.',
  'I am proud of myself — no asterisk.',
  'I am allowed to take up space, beautifully.',
  'My future self is cheering for me.',
  'Grace and grit live together in me.',
  'I am strong in ways I couldn’t have imagined.',
  'I am gentle with myself on the hard days.'
];

// ---------- STATE ----------
var S = {
  _p:'rad_',
  get:function(k){ try{return JSON.parse(localStorage.getItem(this._p+k))}catch(e){return null} },
  set:function(k,v){ localStorage.setItem(this._p+k,JSON.stringify(v)) },
  get startDate(){ var d=this.get('start'); return d?new Date(d):null; },
  set startDate(d){ this.set('start',d.toISOString()); },
  get completed(){ return this.get('done')||{}; },
  setDone:function(ds,v){ var c=this.completed; if(v)c[ds]=true; else delete c[ds]; this.set('done',c); },
  session:function(ds){ return this.get('s_'+ds)||{}; },
  saveSession:function(ds,d){ this.set('s_'+ds,d); },
  badges:function(){ return this.get('badges')||{}; },
  grantBadge:function(id){ var b=this.badges(); if(b[id])return false; b[id]={earnedAt:new Date().toISOString()}; this.set('badges',b); return true; },
  lastWeight:function(exId){
    var all=[];
    for(var i=0;i<localStorage.length;i++){
      var k=localStorage.key(i);
      if(!k||!k.startsWith(this._p+'s_'))continue;
      var d=k.substring((this._p+'s_').length);
      try{
        var s=JSON.parse(localStorage.getItem(k));
        if(s&&s.perf&&s.perf[exId]){
          for(var j=s.perf[exId].length-1;j>=0;j--){
            var p=s.perf[exId][j];
            if(p&&typeof p.w==='number')all.push({d:d,w:p.w});
          }
        }
      }catch(e){}
    }
    all.sort(function(a,b){return a.d<b.d?1:-1;});
    return all.length?all[0].w:null;
  }
};

// ---------- UTILITIES ----------
function ds(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function norm(d){ return new Date(d.getFullYear(),d.getMonth(),d.getDate()); }
function fmt(d){ var days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']; return days[d.getDay()]+', '+mo[d.getMonth()]+' '+d.getDate(); }
function weekStart(d){ var day=d.getDay(); return norm(new Date(d.getFullYear(),d.getMonth(),d.getDate()+(day===0?-6:1-day))); }
function weekDates(off){ var s=weekStart(norm(new Date())); s.setDate(s.getDate()+off*7); return Array.from({length:7},function(_,i){var d=new Date(s);d.setDate(d.getDate()+i);return d;}); }
function phaseFor(date){ if(!S.startDate)return null; var diff=Math.round((norm(date)-norm(S.startDate))/864e5); if(diff<0)return null; var wk=Math.floor(diff/7)+1,cum=0; for(var i=0;i<PHASES.length;i++){var p=PHASES[i];if(wk<=cum+p.weeks)return{phase:p,wip:wk-cum,wk:wk};cum+=p.weeks;} return null; }
function dayOffset(date){ if(!S.startDate)return -1; return Math.round((norm(date)-norm(S.startDate))/864e5); }
function workoutFor(date){
  var pi=phaseFor(date); if(!pi)return null;
  var diff=dayOffset(date),dayIdx=((diff%7)+7)%7,e=pi.phase.schedule[dayIdx];
  if(!e||e.type==='rest')return{type:'rest',pi:pi};
  var w=pi.phase.workouts?pi.phase.workouts[e.wk]:null;
  if(!w){for(var i=0;i<PHASES.length;i++){if(PHASES[i].workouts&&PHASES[i].workouts[e.wk]){w=PHASES[i].workouts[e.wk];break;}}}
  if(!w)return{type:'rest',pi:pi};
  var r={}; for(var k in w)r[k]=w[k]; r.type=e.type; r.pi=pi;
  // Inject home routine per phase cadence
  r.exercises=maybePrependHomeRoutine(r.exercises,pi,dayIdx);
  return r;
}
function maybePrependHomeRoutine(exs,pi,dayIdx){
  var pid=pi.phase.id,show=false;
  if(pid<=3)show=true; // Phases 1-3: every workout day
  else if(pid===4){ // Phase 4: first workout day of the week (lowest non-rest dayIdx)
    var firstWorkoutDay=-1;
    for(var i=0;i<pi.phase.schedule.length;i++){if(pi.phase.schedule[i].type!=='rest'){firstWorkoutDay=i;break;}}
    show=dayIdx===firstWorkoutDay;
  }
  // Phase 5+: not auto, only via Program tab
  if(!show)return exs;
  return hipHomeBlock().concat(exs);
}

// ---------- PLANS ----------
var Plans = {
  _key:'rad_plans',
  getAll:function(){ try{return JSON.parse(localStorage.getItem(this._key))||[];}catch(e){return[];} },
  save:function(name){ var plans=this.getAll(),data={};for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k.startsWith('rad_')&&k!==this._key)data[k]=localStorage.getItem(k);} var idx=plans.findIndex(function(p){return p.name===name;}); var plan={name:name,savedAt:new Date().toISOString(),data:data}; if(idx>=0)plans[idx]=plan;else plans.push(plan); localStorage.setItem(this._key,JSON.stringify(plans)); },
  load:function(name){ var plan=this.getAll().find(function(p){return p.name===name;}); if(!plan)return false; Object.keys(localStorage).filter(function(k){return k.startsWith('rad_')&&k!==Plans._key;}).forEach(function(k){localStorage.removeItem(k);}); for(var k in plan.data)localStorage.setItem(k,plan.data[k]); return true; },
  del:function(name){ localStorage.setItem(this._key,JSON.stringify(this.getAll().filter(function(p){return p.name!==name;}))); },
  reset:function(){ Object.keys(localStorage).filter(function(k){return k.startsWith('rad_')&&k!==Plans._key;}).forEach(function(k){localStorage.removeItem(k);}); }
};

// ---------- APP ----------
var App = {
  tab:'today', woff:0, ntab:'today',
  init:function(){
    var self=this;
    S.set('appver',APP_VERSION); // Don't wipe user data on upgrade; just update the marker.
    document.querySelectorAll('.tab').forEach(function(t){t.addEventListener('click',function(){self.tab=t.dataset.tab;self.woff=0;self.render();});});
    document.getElementById('menu-btn').addEventListener('click',function(){self.showPlansMenu();});
    this.render();
  },
  render:function(){
    var self=this;
    document.querySelectorAll('.tab').forEach(function(t){t.classList.toggle('active',t.dataset.tab===self.tab);});
    var b=document.getElementById('phase-badge');
    if(!S.startDate)b.textContent='BEGIN'; else{var pi=phaseFor(norm(new Date()));b.textContent=pi?pi.phase.name+' · Wk '+pi.wip:'COMPLETE';}
    var el=document.getElementById('content');
    if(this.tab==='today')el.innerHTML=this.rToday();
    else if(this.tab==='calendar')el.innerHTML=this.rCal();
    else if(this.tab==='program')el.innerHTML=this.rProg();
    else if(this.tab==='nourish')el.innerHTML=this.rNourish();
    else if(this.tab==='journey')el.innerHTML=this.rJourney();
    this.bindAll();
  },

  rToday:function(){
    var today=norm(new Date());
    if(!S.startDate)return '<div class="setup"><h2><span class="accent">RADIANCE</span></h2><p class="sub">Your wellness journey starts here</p><div class="card"><p style="font-size:14px;color:var(--muted);line-height:1.7;margin-bottom:20px">A gentle, beautiful program. Four days a week to start. Hip care, feel-good cardio, and strength that makes you feel powerful.</p><div class="form-group"><label>When do you want to start?</label><input type="date" id="start-date" value="'+ds(today)+'"></div><button class="btn-primary" id="setup-btn">BEGIN YOUR JOURNEY</button></div></div>';
    if(today<norm(S.startDate))return '<div class="rest-hero"><h2>Your Journey Begins Soon</h2><p>Your program starts '+fmt(norm(S.startDate))+'. You’re going to feel amazing.</p></div>';
    var w=workoutFor(today);
    if(!w)return '<div class="rest-hero"><h2>You Did It</h2><p>48 weeks. You showed up for yourself again and again. You are radiant.</p></div><div style="text-align:center;margin-top:16px"><button class="btn-secondary" id="reset-btn">Begin Again</button></div>';
    if(w.type==='rest')return '<div class="today-date">'+fmt(today)+'</div><div class="today-phase">'+w.pi.phase.name+' · Week '+w.pi.wip+'</div><div class="rest-hero"><h2>Rest & Restore</h2><p>Your body gets stronger on rest days. Water, good food, something that makes you smile.</p></div><div class="card"><div class="section-title">Rest Day Ideas</div><ul class="tip-list"><li>Gentle walk outside</li><li>Extra water</li><li>Early bedtime</li><li>Massage gun on glutes if anything feels tight</li></ul></div>';
    return this.rWorkout(w,today);
  },

  rWorkout:function(w,date){
    var self=this,d=ds(date),ses=S.session(d),done=S.completed[d];
    var h='<div class="today-date">'+fmt(date)+'</div><div class="today-phase">'+w.pi.phase.name+' · Week '+w.pi.wip+'</div><div class="today-title">'+w.name+'</div><div class="today-focus '+(w.type==='cardio'?'cardio-focus':'tone-focus')+'">'+w.focus+' · '+w.dur+'</div>';
    // Crunch card on cardio days
    if(w.type==='cardio')h+=this.rCrunchCard(date);
    var cardioBlockIdx=0;
    w.exercises.forEach(function(ex,i){
      if(ex.section){h+='<div class="section-marker">'+ex.section+'</div>';return;}
      if(ex.type==='massage'){h+=self.rMassage();return;}
      if(ex.type==='cardio'){h+=self.rCardioBlock(ex,i,cardioBlockIdx,d,ses);cardioBlockIdx++;return;}
      if(ex.id){h+=self.rExerciseBlock(ex,i,d,ses);return;}
    });
    // Cool-down line (stretches removed; keep it short + positive)
    h+='<div class="card" style="margin-top:12px;text-align:center;font-size:13px;color:var(--muted);line-height:1.6">Walk it out for a couple of minutes. Deep breaths. Big water.</div>';
    h+='<button class="btn-complete'+(done?' completed':'')+'" id="complete-btn">'+(done?'COMPLETE ✓':'COMPLETE WORKOUT')+'</button>';
    return h;
  },

  rCrunchCard:function(date){
    var dow=date.getDay(); // 0=Sun 6=Sat
    var hoursByDow=['7am – 7pm','5am – 11pm','5am – 11pm','5am – 11pm','5am – 11pm','5am – 10pm','7am – 7pm'];
    var todayHours=hoursByDow[dow];
    return '<div class="card crunch-card"><div class="crunch-head"><span class="crunch-icon">🏋️‍♀️</span><div class="crunch-title">Crunch Allen</div></div><div class="crunch-sub">Today’s hours · '+todayHours+'</div><div class="crunch-sub">510 N Watters Rd · 469.824.3022</div><a href="https://www.crunch.com/locations/allen" target="_blank" class="crunch-link">See Today’s Classes →</a></div>';
  },

  rMassage:function(){
    var h='<div class="card massage-card"><div class="section-title" style="margin-top:0;color:var(--primary)">Massage Gun Protocol</div><p style="font-size:12px;color:var(--muted);margin-bottom:10px;line-height:1.5">Do this BEFORE the hip work. Trigger-point release first, then activation.</p>';
    MASSAGE.forEach(function(m){h+='<div class="massage-row"><span class="massage-name">'+m.name+'</span><span class="massage-time">'+m.time+'</span><div class="massage-note">'+m.note+'</div></div>';});
    h+='</div>';
    return h;
  },

  rCardioBlock:function(ex,i,blockIdx,d,ses){
    var chosen=ses.machines&&ses.machines[blockIdx]||ex.fixed||null;
    var chosenObj=chosen?MACHINES.find(function(m){return m.id===chosen;}):null;
    var patternText=CARDIO_PATTERNS[ex.pattern]||'';
    var h='<div class="cardio-block">';
    h+='<div class="cardio-target"><span class="cardio-dur">'+ex.duration+' min</span>';
    if(patternText)h+='<span class="cardio-pattern">'+patternText+'</span>';
    h+='</div>';
    if(ex.note)h+='<div class="exercise-note">'+ex.note+'</div>';
    if(ex.fixed){
      h+='<div class="machine-fixed"><span class="machine-emoji">'+chosenObj.emoji+'</span><span>'+chosenObj.label+' · '+chosenObj.cue+'</span></div>';
    } else {
      h+='<div class="machine-picker" data-block="'+blockIdx+'">';
      MACHINES.forEach(function(m){
        h+='<button class="machine-pill'+(chosen===m.id?' selected':'')+'" data-machine="'+m.id+'" data-block="'+blockIdx+'"><span class="machine-emoji">'+m.emoji+'</span>'+m.label+'</button>';
      });
      h+='</div>';
      if(chosenObj)h+='<div class="machine-cue">'+chosenObj.cue+'</div>';
    }
    h+='</div>';
    return h;
  },

  rExerciseBlock:function(ex,i,d,ses){
    var info=EX[ex.id]; if(!info)return '';
    var isTimeBased=typeof ex.time==='number',numSets=ex.sets||1;
    var eachLabel=ex.each?' each side':'';
    var rxText=isTimeBased?(numSets+' × '+ex.time+'s'+eachLabel):(numSets+' × '+ex.reps+eachLabel);
    var perf=(ses.perf&&ses.perf[ex.id])||[];
    var h='<div class="exercise"><div class="exercise-header"><span class="exercise-name" data-exid="'+ex.id+'">'+info.name+'</span><span class="exercise-rx">'+rxText+'</span></div>';
    if(ex.note)h+='<div class="exercise-note">'+ex.note+'</div>';
    if(isTimeBased){
      h+='<div class="set-list">';
      for(var s=0;s<numSets;s++){
        var isDone=perf[s]&&perf[s].done;
        h+='<div class="set-row time-row'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'"><span class="set-num">'+(s+1)+'</span><span class="set-time">'+ex.time+' seconds</span><button class="set-check'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'" data-mode="time">✓</button></div>';
      }
      h+='</div>';
    } else if(info.defaultBase>0){
      var lastW=S.lastWeight(ex.id),suggestedW=lastW!==null?lastW:info.defaultBase;
      h+='<div class="set-list">';
      for(var s=0;s<numSets;s++){
        var p=perf[s]||null,isDone=!!p;
        var wVal=p?p.w:'',rVal=p?p.r:'',wPh=suggestedW?String(suggestedW):'',rPh=String(ex.reps||'');
        h+='<div class="set-row'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'"><span class="set-num">'+(s+1)+'</span><input type="number" class="set-wt" data-exid="'+ex.id+'" data-set="'+s+'" value="'+wVal+'" placeholder="'+wPh+'" inputmode="decimal"><span class="set-x">×</span><input type="number" class="set-reps" data-exid="'+ex.id+'" data-set="'+s+'" value="'+rVal+'" placeholder="'+rPh+'" inputmode="numeric"><button class="set-check'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'" data-mode="weight">✓</button></div>';
      }
      h+='</div>';
      var unitLabel=info.unit==='each'?'each DB':'total';
      h+='<div class="set-hint-row"><span class="set-hint">'+unitLabel+'</span></div>';
    } else {
      // bodyweight reps, no weight input
      h+='<div class="set-list">';
      for(var s=0;s<numSets;s++){
        var p=perf[s]||null,isDone=!!p;
        h+='<div class="set-row bw-row'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'"><span class="set-num">'+(s+1)+'</span><span class="set-bw">'+(ex.reps||'')+' reps'+eachLabel+'</span><button class="set-check'+(isDone?' done':'')+'" data-exid="'+ex.id+'" data-set="'+s+'" data-mode="bw">✓</button></div>';
      }
      h+='</div>';
    }
    h+='</div>';
    return h;
  },

  rCal:function(){
    var dates=weekDates(this.woff),today=ds(norm(new Date())),done=S.completed,dn=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    var s1=dates[0].toLocaleDateString('en',{month:'short',day:'numeric'}),s2=dates[6].toLocaleDateString('en',{month:'short',day:'numeric'});
    var h='<div class="week-nav"><button data-dir="-1">←</button><span>'+s1+' – '+s2+'</span><button data-dir="1">→</button></div>';
    dates.forEach(function(d,i){
      var dd=ds(d),w=S.startDate?workoutFor(d):null,isT=dd===today,isD=done[dd];
      var badge='',nm='',det='';
      if(!w||!S.startDate)nm='Not Started';
      else if(!phaseFor(d))nm='Journey Complete';
      else if(w.type==='rest'){nm='Rest & Restore';det='Recovery';}
      else if(w.type==='cardio'){badge='<span class="badge badge-cardio">CARDIO</span>';nm=w.name;det=w.focus;}
      else if(w.type==='tone'){badge='<span class="badge badge-tone">TONE</span>';nm=w.name;det=w.focus;}
      h+='<div class="day-card'+(isT?' today':'')+(isD?' completed':'')+'" data-date="'+dd+'"><div class="day-date"><div class="dow">'+dn[i]+'</div><div class="dom">'+d.getDate()+'</div></div><div class="day-info"><div class="dw">'+nm+' '+badge+'</div><div class="dd">'+det+'</div></div>'+(isD?'<div class="day-check">✓</div>':'')+'</div>';
    });
    return h;
  },

  rProg:function(){
    var pi=S.startDate?phaseFor(norm(new Date())):null,tot=PHASES.reduce(function(s,p){return s+p.weeks;},0);
    var cw=pi?pi.wk:(S.startDate?tot+1:0),pct=S.startDate?Math.min(cw/tot*100,100):0;
    var startDow=S.startDate?norm(S.startDate).getDay():3,dns=['Su','Mo','Tu','We','Th','Fr','Sa'];
    var dlab=Array.from({length:7},function(_,i){return dns[(startDow+i)%7];});
    var h='<div class="section-title">Your Journey</div><div class="progress-bar"><div class="progress-fill" style="width:'+pct+'%"></div></div><div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:16px"><span>Week '+Math.min(cw,tot)+' of '+tot+'</span><span>'+Math.round(pct)+'%</span></div>';
    // Hip home quick-access card
    h+='<div class="card hip-access"><div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><div><div style="font-weight:700;font-size:14px">Hip Home Routine</div><div style="font-size:11px;color:var(--muted);margin-top:2px">Anytime your hip needs love</div></div><button class="btn-secondary" id="hip-routine-btn" style="padding:8px 14px;font-size:12px">Open</button></div></div>';
    PHASES.forEach(function(p){
      var cur=pi&&pi.phase.id===p.id,past=pi&&pi.phase.id>p.id,allDone=!pi&&S.startDate;
      h+='<div class="phase-card'+(cur?' current':'')+(past||allDone?' past':'')+'"><div class="phase-hdr"><span class="phase-name">'+p.name+'</span><span class="phase-wk">Wks '+p.startWeek+'–'+(p.startWeek+p.weeks-1)+'</span></div><div class="phase-tag">'+p.tag+'</div><div class="phase-desc">'+p.desc+'</div><div class="phase-sched">'+p.schedule.map(function(e,idx){var t=e?e.type:'rest';return '<div class="phase-sched-day '+t+'"><div class="dl">'+dlab[idx]+'</div><div>'+(t==='cardio'?'C':t==='tone'?'T':'–')+'</div></div>';}).join('')+'</div><div style="margin-top:8px;font-size:12px;color:var(--dim)">'+p.cardioDays+' cardio · '+p.toneDays+' tone · '+(7-p.cardioDays-p.toneDays)+' rest</div></div>';
    });
    if(S.startDate)h+='<div style="text-align:center;margin-top:20px"><button class="btn-secondary" id="reset-btn" style="color:var(--danger);border-color:var(--danger)">Reset Journey</button></div>';
    return h;
  },

  rNourish:function(){
    var today=norm(new Date()),w=S.startDate?workoutFor(today):null,dt=w?(w.type==='rest'?'rest':w.type):'rest';
    var h='<div class="sub-tabs"><button class="sub-tab'+(this.ntab==='today'?' active':'')+'" data-st="today">Today</button><button class="sub-tab'+(this.ntab==='meals'?' active':'')+'" data-st="meals">Meals</button><button class="sub-tab'+(this.ntab==='snacks'?' active':'')+'" data-st="snacks">Snacks</button><button class="sub-tab'+(this.ntab==='wellness'?' active':'')+'" data-st="wellness">Wellness</button></div>';
    if(this.ntab==='today'){
      var bl=dt==='cardio'?'badge-cardio':dt==='tone'?'badge-tone':'badge-rest',lb=dt==='cardio'?'Cardio Day':dt==='tone'?'Toning Day':'Rest Day';
      h+='<div class="card"><span class="badge '+bl+'">'+lb+'</span><p style="font-size:14px;line-height:1.7;margin-top:12px">'+NOURISH.dayFocus[dt]+'</p></div>';
      h+='<div class="card"><div class="section-title">Focus</div><ul class="tip-list"><li>Start every meal with protein</li><li>Add colorful veggies</li><li>Drink water before each meal</li><li>Choose smart snacks between meals</li></ul></div>';
      h+='<div class="card"><div class="section-title">Hydration</div><ul class="tip-list">'+NOURISH.hydration.slice(0,3).map(function(t){return '<li>'+t+'</li>';}).join('')+'</ul></div>';
    } else if(this.ntab==='meals'){
      NOURISH.meals.forEach(function(m){h+='<div class="meal"><div class="meal-name">'+m.name+'</div><div class="meal-note">'+m.note+'</div><ul class="meal-examples">'+m.ex.map(function(e){return '<li>'+e+'</li>';}).join('')+'</ul></div>';});
    } else if(this.ntab==='snacks'){
      h+='<div class="card"><div class="section-title">Smart Swaps</div><p style="font-size:13px;color:var(--muted);margin-bottom:12px">Same satisfaction, better nourishment:</p>';
      NOURISH.snacks.forEach(function(s){h+='<div class="snack-swap"><span class="snack-old">'+s.old+'</span><span class="snack-arrow">→</span><span class="snack-new">'+s.better+'</span></div>';});
      h+='</div>';
    } else if(this.ntab==='wellness'){
      h+='<div class="card"><div class="section-title">Nourishing Your Radiance</div><ul class="tip-list">'+NOURISH.wellness.map(function(t){return '<li>'+t+'</li>';}).join('')+'</ul></div>';
      h+='<div class="card"><div class="section-title">Hydration</div><ul class="tip-list">'+NOURISH.hydration.map(function(t){return '<li>'+t+'</li>';}).join('')+'</ul></div>';
    }
    return h;
  },

  rJourney:function(){
    var done=S.completed,total=Object.keys(done).length,streak=0;
    for(var i=0;i<200;i++){var d=new Date();d.setDate(d.getDate()-i);var dd=ds(norm(d)),w=S.startDate?workoutFor(norm(d)):null;if(w&&w.type&&w.type!=='rest'){if(done[dd])streak++;else if(i>0)break;}}
    var wd=weekDates(0),eS=0,eC=0; wd.forEach(function(d){var ses=S.session(ds(d));if(ses.energy){eS+=ses.energy;eC++;}});
    var aE=eC?Math.round(eS/eC*10)/10:0,eL=['','Low','OK','Good','Great','Amazing'];
    // Affirmation of the day (rotates by date)
    var today=new Date(),seed=today.getFullYear()*1000+today.getMonth()*31+today.getDate();
    var aff=AFFIRMATIONS[seed%AFFIRMATIONS.length];
    var h='<div class="affirmation">“'+aff+'”</div>';
    h+='<div class="streak"><div class="streak-num">'+streak+'</div><div class="streak-lbl">Workout Streak</div></div>';
    h+='<div class="card" style="text-align:center"><div style="font-size:36px;font-weight:800;color:var(--primary)">'+total+'</div><div style="font-size:13px;color:var(--muted)">Workouts Completed</div></div>';
    if(aE>0)h+='<div class="card" style="text-align:center"><div class="section-title">This Week’s Energy</div><div style="font-size:24px;font-weight:700;color:var(--primary)">'+aE+' / 5</div><div style="font-size:13px;color:var(--muted)">'+eL[Math.round(aE)]+'</div></div>';
    // Badge grid
    var earned=S.badges();
    h+='<div class="card"><div class="section-title">Badges</div><div class="badge-grid">';
    COUNT_BADGES.forEach(function(b){
      var e=!!earned[b.id];
      h+='<div class="badge-item'+(e?' earned':' locked')+'"><div class="badge-icon">'+(e?b.icon:'🔒')+'</div><div class="badge-name">'+b.name+'</div><div class="badge-sub">'+b.n+' workouts</div></div>';
    });
    h+='</div></div>';
    return h;
  },

  bindAll:function(){
    var self=this;
    document.querySelectorAll('.sub-tab').forEach(function(t){t.addEventListener('click',function(){self.ntab=t.dataset.st;self.render();});});
    document.querySelectorAll('.week-nav button').forEach(function(b){b.addEventListener('click',function(){self.woff+=parseInt(b.dataset.dir);self.render();});});
    var sb=document.getElementById('setup-btn');
    if(sb)sb.addEventListener('click',function(){var di=document.getElementById('start-date');if(!di||!di.value)return;var p=di.value.split('-');S.startDate=new Date(parseInt(p[0]),parseInt(p[1])-1,parseInt(p[2]));self.render();});
    var cb=document.getElementById('complete-btn');
    if(cb)cb.addEventListener('click',function(){
      var d=ds(norm(new Date())),wasDone=S.completed[d];
      S.setDone(d,!wasDone);
      if(!wasDone){self.onWorkoutComplete(d);}
      else self.render();
    });
    // Machine pill picker
    document.querySelectorAll('.machine-pill').forEach(function(p){p.addEventListener('click',function(){
      var d=ds(norm(new Date())),ses=S.session(d),block=parseInt(p.dataset.block),machine=p.dataset.machine;
      if(!ses.machines)ses.machines={};
      ses.machines[block]=machine;
      S.saveSession(d,ses);
      self.render();
    });});
    // Per-set completion with weight/reps inputs
    document.querySelectorAll('.set-check').forEach(function(b){b.addEventListener('click',function(){
      var exId=b.dataset.exid,si=parseInt(b.dataset.set),mode=b.dataset.mode,d=ds(norm(new Date())),ses=S.session(d);
      if(!ses.perf)ses.perf={};
      if(!ses.perf[exId])ses.perf[exId]=[];
      while(ses.perf[exId].length<=si)ses.perf[exId].push(null);
      if(ses.perf[exId][si]){
        ses.perf[exId][si]=null;
      } else {
        if(mode==='weight'){
          var wInput=document.querySelector('.set-wt[data-exid="'+exId+'"][data-set="'+si+'"]'),rInput=document.querySelector('.set-reps[data-exid="'+exId+'"][data-set="'+si+'"]');
          var w=wInput&&wInput.value?parseFloat(wInput.value):(wInput&&wInput.placeholder?parseFloat(wInput.placeholder):null);
          var r=rInput&&rInput.value?parseInt(rInput.value):(rInput&&rInput.placeholder?parseInt(rInput.placeholder):null);
          ses.perf[exId][si]={w:isNaN(w)?null:w,r:isNaN(r)?null:r};
        } else if(mode==='time'){
          ses.perf[exId][si]={done:true};
        } else {
          ses.perf[exId][si]={done:true};
        }
      }
      S.saveSession(d,ses);
      self.render();
    });});
    document.querySelectorAll('.exercise-name').forEach(function(el){el.addEventListener('click',function(){self.showExInfo(el.dataset.exid);});});
    document.querySelectorAll('.day-card').forEach(function(c){c.addEventListener('click',function(){self.showDay(c.dataset.date);});});
    var rb=document.getElementById('reset-btn');
    if(rb)rb.addEventListener('click',function(){if(confirm('Start fresh? Saved plans are kept.')){Plans.reset();self.render();}});
    var hrb=document.getElementById('hip-routine-btn');
    if(hrb)hrb.addEventListener('click',function(){self.showHipRoutine();});
  },

  onWorkoutComplete:function(dateStr){
    var self=this;
    // Pick celebration
    var msg=CELEBRATIONS[Math.floor(Math.random()*CELEBRATIONS.length)];
    // Check for new badges
    var total=Object.keys(S.completed).length,newBadge=null;
    for(var i=0;i<COUNT_BADGES.length;i++){
      var b=COUNT_BADGES[i];
      if(total>=b.n&&S.grantBadge(b.id)){newBadge=b;break;}
    }
    this.showCelebration(msg,newBadge,dateStr);
  },

  showCelebration:function(msg,badge,dateStr){
    var self=this,ov=document.getElementById('overlay');
    ov.classList.remove('hidden');
    var badgeHTML='';
    if(badge)badgeHTML='<div class="badge-unlock"><div class="badge-unlock-title">Badge unlocked!</div><div class="badge-unlock-icon">'+badge.icon+'</div><div class="badge-unlock-name">'+badge.name+'</div><div class="badge-unlock-msg">'+badge.msg+'</div></div>';
    ov.innerHTML='<div class="overlay-content celebration"><div class="petals"><span>✨</span><span>🌸</span><span>✨</span><span>🌹</span><span>✨</span></div><div class="celebration-msg">'+msg+'</div>'+badgeHTML+'<button class="btn-primary" id="cel-next">Rate Your Energy</button></div>';
    document.getElementById('cel-next').addEventListener('click',function(){self.showEnergy(dateStr);});
    ov.addEventListener('click',function(e){if(e.target===ov){ov.classList.add('hidden');self.render();}});
  },

  showEnergy:function(dateStr){
    var self=this,ov=document.getElementById('overlay');ov.classList.remove('hidden');
    ov.innerHTML='<div class="overlay-content" style="text-align:center"><h3 style="margin-bottom:8px;color:var(--primary)">How do you feel?</h3><p style="font-size:13px;color:var(--muted);margin-bottom:16px">Rate your energy</p><div class="energy-row"><button class="energy-btn" data-e="1">1</button><button class="energy-btn" data-e="2">2</button><button class="energy-btn" data-e="3">3</button><button class="energy-btn" data-e="4">4</button><button class="energy-btn" data-e="5">5</button></div><div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:16px;padding:0 4px"><span>Low</span><span>Amazing</span></div><button class="close-btn" id="skip-energy">Skip</button></div>';
    document.querySelectorAll('.energy-btn').forEach(function(b){b.addEventListener('click',function(){var ses=S.session(dateStr);ses.energy=parseInt(b.dataset.e);S.saveSession(dateStr,ses);ov.classList.add('hidden');self.render();});});
    document.getElementById('skip-energy').addEventListener('click',function(){ov.classList.add('hidden');self.render();});
    ov.addEventListener('click',function(e){if(e.target===ov){ov.classList.add('hidden');self.render();}});
  },

  showExInfo:function(id){
    var ex=EX[id];if(!ex)return;
    var ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var primary=(ex.primary||[]).map(function(m){return '<span class="muscle-tag primary">'+m+'</span>';}).join('');
    var secondary=(ex.secondary||[]).map(function(m){return '<span class="muscle-tag">'+m+'</span>';}).join('');
    var formList=(ex.form||[]).map(function(s){return '<li>'+s+'</li>';}).join('');
    var equipLine=ex.equip?'<div class="ex-equip"><strong>Equipment:</strong> '+ex.equip+'</div>':'';
    ov.innerHTML='<div class="overlay-content ex-info"><h3>'+ex.name+'</h3><div class="muscle-tags">'+primary+secondary+'</div>'+equipLine+'<a href="'+ex.yt+'" target="_blank" class="yt-link" style="margin-bottom:12px;margin-top:8px">▶ Watch Form Demo on YouTube</a><ol class="form-steps">'+formList+'</ol><button class="close-btn" id="close-ov">Got it</button></div>';
    document.getElementById('close-ov').addEventListener('click',function(){ov.classList.add('hidden');});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.classList.add('hidden');});
  },

  showHipRoutine:function(){
    var self=this,ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var h='<div class="overlay-content"><h3>Hip Home Routine</h3><p style="font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.5">Any time your hip needs attention. Do the massage gun first, then the four exercises.</p>';
    h+='<div class="section-marker">Massage Gun</div>';
    MASSAGE.forEach(function(m){h+='<div class="massage-row"><span class="massage-name">'+m.name+'</span><span class="massage-time">'+m.time+'</span><div class="massage-note">'+m.note+'</div></div>';});
    h+='<div class="section-marker">Hip Exercises</div>';
    hipHomeBlock().filter(function(e){return e.id;}).forEach(function(ex){
      var info=EX[ex.id];
      var eachL=ex.each?' each side':'';
      h+='<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between;align-items:center"><a href="'+info.yt+'" target="_blank" style="font-weight:600;font-size:14px;color:var(--primary);text-decoration:none">'+info.name+' →</a><span style="font-size:12px;color:var(--muted)">'+ex.sets+' × '+ex.reps+eachL+'</span></div></div>';
    });
    h+='<button class="close-btn" id="close-ov">Got it</button></div>';
    ov.innerHTML=h;
    document.getElementById('close-ov').addEventListener('click',function(){ov.classList.add('hidden');});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.classList.add('hidden');});
  },

  showDay:function(dateStr){
    var parts=dateStr.split('-'),date=new Date(parseInt(parts[0]),parseInt(parts[1])-1,parseInt(parts[2]));
    var w=S.startDate?workoutFor(date):null;if(!w||w.type==='rest')return;
    var ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var c='<div class="overlay-content"><h3>'+w.name+'</h3><div style="font-size:13px;color:var(--muted);margin-bottom:12px">'+w.focus+' · '+w.dur+'</div>';
    w.exercises.forEach(function(ex){
      if(ex.section){c+='<div class="section-marker">'+ex.section+'</div>';return;}
      if(ex.type==='massage'){c+='<div style="font-size:12px;color:var(--primary);padding:6px 0"><strong>Massage gun</strong> · glute max, glute medius, inner thigh · 30s each side</div>';return;}
      if(ex.type==='cardio'){c+='<div style="padding:6px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between"><span style="font-weight:600;font-size:13px">Cardio (your choice)</span><span style="color:var(--muted);font-size:12px">'+ex.duration+' min</span></div>'+(ex.note?'<div style="font-size:11px;color:var(--muted);margin-top:2px">'+ex.note+'</div>':'')+'</div>';return;}
      if(ex.id){
        var info=EX[ex.id];if(!info)return;
        var rx=typeof ex.time==='number'?(ex.sets+'×'+ex.time+'s'):(ex.sets+'×'+ex.reps+(ex.each?' ea':''));
        c+='<div style="padding:6px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between"><span style="font-weight:600;font-size:13px">'+info.name+'</span><span style="color:var(--muted);font-size:12px">'+rx+'</span></div></div>';
      }
    });
    c+='<button class="close-btn" id="close-ov">Close</button></div>';
    ov.innerHTML=c;
    document.getElementById('close-ov').addEventListener('click',function(){ov.classList.add('hidden');});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.classList.add('hidden');});
  },

  showPlansMenu:function(){
    var self=this,ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var plans=Plans.getAll(),hasData=!!S.startDate,pi=hasData?phaseFor(norm(new Date())):null;
    var h='<div class="overlay-content"><h3 style="margin-bottom:16px">Plans</h3>';
    if(hasData)h+='<div class="section-title">Current</div><div style="font-size:13px;margin-bottom:12px">Started: '+fmt(norm(S.startDate))+'<br>'+(pi?pi.phase.name+' · Week '+pi.wip:'Complete')+'</div>';
    if(hasData)h+='<div class="section-title">Save</div><div style="display:flex;gap:8px;margin-bottom:16px"><input type="text" id="plan-name-in" placeholder="Plan name" style="flex:1;padding:8px;background:var(--bg);border:1px solid var(--border);border-radius:var(--rs);color:var(--text);font-size:13px"><button id="save-plan-btn" style="padding:8px 16px;background:var(--primary);color:#fff;border:none;border-radius:var(--rs);font-size:13px;font-weight:700;cursor:pointer">Save</button></div>';
    h+='<div class="section-title">Saved</div>';
    if(plans.length)plans.forEach(function(p){var d=new Date(p.savedAt).toLocaleDateString('en',{month:'short',day:'numeric',year:'numeric'});h+='<div class="plan-item"><div><div class="plan-item-name">'+p.name+'</div><div class="plan-item-date">'+d+'</div></div><div class="plan-item-btns"><button class="plan-btn-load" data-pn="'+p.name+'">Load</button><button class="plan-btn-del" data-pn="'+p.name+'">Del</button></div></div>';});
    else h+='<div style="font-size:13px;color:var(--dim);padding:8px 0">No saved plans yet.</div>';
    h+='<div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)"><button id="new-plan-btn" style="width:100%;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:var(--rs);color:var(--text);font-size:13px;font-weight:600;cursor:pointer">New Journey</button></div><button class="close-btn" id="close-ov">Close</button></div>';
    ov.innerHTML=h;
    var closeOv=function(){ov.classList.add('hidden');};
    document.getElementById('close-ov').addEventListener('click',closeOv);
    ov.addEventListener('click',function(e){if(e.target===ov)closeOv();});
    var svb=document.getElementById('save-plan-btn');if(svb)svb.addEventListener('click',function(){var n=document.getElementById('plan-name-in').value.trim();if(!n)return;Plans.save(n);self.showPlansMenu();});
    document.querySelectorAll('.plan-btn-load').forEach(function(b){b.addEventListener('click',function(){if(confirm('Load \"'+b.dataset.pn+'\"?')){Plans.load(b.dataset.pn);closeOv();self.render();}});});
    document.querySelectorAll('.plan-btn-del').forEach(function(b){b.addEventListener('click',function(){if(confirm('Delete \"'+b.dataset.pn+'\"?')){Plans.del(b.dataset.pn);self.showPlansMenu();}});});
    document.getElementById('new-plan-btn').addEventListener('click',function(){if(!hasData||confirm('Start fresh?')){Plans.reset();closeOv();self.render();}});
  }
};

document.addEventListener('DOMContentLoaded',function(){App.init();});
