// ============================================================
// RADIANCE v3 — 48-Week Women's Wellness Program
// Evidence-based: GLP-1 aware, periodized cardio + strength
// hip rehab protocol, progressive 3->4->5 day schedule
// ============================================================
const APP_VERSION = 5;

const EX = {
  stair_int:{name:'Stair Stepper Intervals',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+stair+stepper+interval+workout',form:['Stand tall, light grip on rails','Increase speed for work intervals, drop for rest','Breathe rhythmically','Full steps, press through whole foot']},
  stair_ss:{name:'Stair Stepper Steady',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+stair+stepper+steady+state+fat+burn',form:['Find a pace you can hold while talking','Stand tall, core engaged','Full steps','Should feel like a brisk walk up stairs']},
  tread_inc:{name:'Incline Walk Intervals',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+incline+treadmill+walking+intervals',form:['Speed 3.0-3.5 mph, brisk walk','Alternate high/low incline every 2 min','NEVER hold max incline — always interval it','Light hand touch on rails for balance only']},
  elliptical:{name:'Elliptical',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+elliptical+workout+beginner',form:['Stand tall, push and pull with arms','Try forward AND backward pedaling','Backward targets glutes more','Low impact, easy on hips']},
  bike:{name:'Stationary Bike',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+stationary+bike+workout+beginner',form:['Adjust seat: slight knee bend at bottom','Sit tall, relax shoulders','Easiest machine on your joints','Great on days when things feel sore']},
  rower:{name:'Rowing Machine',cat:'cardio',yt:'https://www.youtube.com/results?search_query=female+rowing+machine+beginner+form',form:['Drive with LEGS first, then lean back, then arms','Return: arms, lean, bend knees','80% legs, 20% arms','Excellent full-body cardio']},
  trap_dl:{name:'Trap Bar Deadlift',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+trap+bar+deadlift+form',form:['Stand centered, feet hip-width','Hinge at hips, grip handles, flat back','Drive through feet to stand','Squeeze glutes at top']},
  goblet:{name:'Goblet Squat',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+goblet+squat+form',form:['Hold dumbbell at chest','Feet shoulder width, toes slightly out','Only go as deep as comfortable','Push through whole foot to stand']},
  db_lunge:{name:'Reverse Lunge',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+reverse+lunge+dumbbell+form',form:['Step BACKWARD (easier on knees)','Lower until both knees ~90 degrees','Push through front heel','Bodyweight is fine to start']},
  hip_thrust:{name:'Hip Thrust',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+hip+thrust+glutes+form',form:['Upper back on bench, feet flat','Drive hips up squeezing glutes HARD','Pause at top 2 seconds','The best glute exercise there is']},
  db_bench:{name:'Dumbbell Bench Press',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+dumbbell+bench+press+form',form:['Lie flat, feet on floor','Dumbbells at chest, press up','Lower slowly, feel the stretch']},
  db_row:{name:'Dumbbell Row',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+one+arm+dumbbell+row+form',form:['One hand on bench, pull dumbbell to hip','Squeeze shoulder blade at top','Lower with control','Builds a strong toned back']},
  db_shoulder:{name:'Shoulder Press',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+dumbbell+shoulder+press+seated',form:['Seated, dumbbells at shoulders','Press up overhead','Lower to shoulders','Keep core tight']},
  pushup:{name:'Push-Up',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+push+up+modified+beginner',form:['From knees or toes — both great','Hands wider than shoulders','Lower chest to floor, push up','Modified is smart, not easy']},
  db_curl:{name:'Bicep Curl',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+bicep+curl+toning',form:['Dumbbells at sides, palms forward','Curl up keeping elbows at sides','Squeeze at top, lower slowly']},
  tri_kick:{name:'Tricep Kickback',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+tricep+kickback+toning',form:['Hinge forward, elbow bent 90 degrees','Extend arm straight back','Squeeze tricep','Tones back of the arm']},
  lat_raise:{name:'Lateral Raise',cat:'tone',yt:'https://www.youtube.com/results?search_query=female+lateral+raise+shoulders',form:['Light dumbbells at sides','Raise to sides until parallel','Slight elbow bend','Use lighter than you think']},
  clamshell:{name:'Clamshell',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+clamshell+exercise+glute+medius',form:['Lie on side, knees bent 45 degrees','Open top knee keeping feet together','Squeeze SIDE of hip — that is the glute medius','#1 exercise for hip pain']},
  side_raise_hip:{name:'Side-Lying Leg Raise',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+side+lying+leg+raise+hip+abduction',form:['Lie on side, raise top leg leading with heel','Keep toes forward, not up','Lower slowly','Targets glute medius']},
  band_walk:{name:'Banded Lateral Walk',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+banded+lateral+walk+glute',form:['Mini band above knees','Slight squat, step sideways','Keep tension on band','10 steps each direction']},
  fire_hydrant:{name:'Fire Hydrant',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+fire+hydrant+exercise+glute',form:['Hands and knees','Lift knee out to side','Squeeze at top','Great for hip mobility + glute med']},
  sl_bridge:{name:'Single-Leg Bridge',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+single+leg+glute+bridge',form:['One foot flat, other leg extended','Drive hips up with grounded leg','Squeeze glute at top','Both legs if too hard']},
  hip_circle:{name:'Hip Circles',cat:'hip',yt:'https://www.youtube.com/results?search_query=female+hip+circles+warm+up+mobility',form:['Stand on one leg, circles with other','10 forward, 10 backward','Warms up hip joint']},
  plank:{name:'Plank',cat:'core',yt:'https://www.youtube.com/results?search_query=female+plank+form+beginner',form:['Forearms on floor, straight line','Squeeze glutes and core','On knees is valid','Breathe!']},
  dead_bug:{name:'Dead Bug',cat:'core',yt:'https://www.youtube.com/results?search_query=female+dead+bug+core+exercise',form:['On back, arms up, knees bent 90','Extend opposite arm and leg slowly','Keep lower back pressed to floor']},
  bird_dog:{name:'Bird Dog',cat:'core',yt:'https://www.youtube.com/results?search_query=female+bird+dog+core+exercise',form:['Hands and knees','Extend opposite arm and leg','Hold 1-2 seconds','Keep hips level']},
  side_plank:{name:'Side Plank',cat:'core',yt:'https://www.youtube.com/results?search_query=female+side+plank+beginner',form:['On side, forearm on floor','Lift hips','From knees is great','Strengthens obliques + hip stabilizers']},
  bike_crunch:{name:'Bicycle Crunch',cat:'core',yt:'https://www.youtube.com/results?search_query=female+bicycle+crunch+form',form:['On back, hands behind head','Opposite elbow to knee','Slow and controlled']},
  pigeon:{name:'Pigeon Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+pigeon+stretch+hip+opener',form:['One knee forward, other leg back','Sink hips toward floor','Hold and breathe','Targets piriformis directly']},
  figure4:{name:'Figure-4 Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+figure+4+stretch+hip',form:['On back, cross ankle over knee','Pull uncrossed leg toward chest','Gentler than pigeon']},
  piriformis_str:{name:'Piriformis Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+piriformis+stretch+seated+sciatica',form:['Seated, cross ankle over knee','Lean forward gently','Hold 30s each side','Do multiple times daily if hip hurts']},
  hip_flexor:{name:'Hip Flexor Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+hip+flexor+stretch+kneeling',form:['Kneel on one knee','Push hips gently forward','Tight hip flexors cause hip pain']},
  cat_cow:{name:'Cat-Cow',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+cat+cow+stretch+spine+mobility',form:['Hands and knees','Arch up (cat), drop belly (cow)','Flow with breath','Wonderful for spine and stress']},
  quad_str:{name:'Quad Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+standing+quad+stretch',form:['Stand on one leg, grab foot behind','Pull heel toward glute','Hold wall for balance']},
  ham_str:{name:'Hamstring Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=female+hamstring+stretch+standing',form:['Heel on low step, leg straight','Hinge forward at hips','Feel stretch behind knee']}
};

// ---- PHASES: 3 days wk1-8, 4 days wk9-36, 4 days wk37-48 ----
const PHASES = [
  {id:1,name:'Spark',tag:'Your beautiful beginning',weeks:4,cardioDays:3,toneDays:1,
    desc:'Four days a week. Two cardio days and two strength days to find your rhythm. Two strength sessions to keep your muscles strong and toned while your body transforms. Hip care woven into every session.',
    prog:'Cardio: 25 min steady state. Strength: light weight, 3x10-12, RPE 6 (comfortable). Hip rehab: full protocol every session.',
    schedule:[{type:'cardio',wk:'s_cardio'},{type:'tone',wk:'s_full_a'},{type:'rest'},{type:'cardio',wk:'s_cardio2'},{type:'cardio',wk:'k_cardio'},{type:'rest'},{type:'rest'}],
    workouts:{
      s_full_a:{name:'Strength + Hip Care',focus:'Full Body \u00b7 Gym',dur:'40 min',exercises:[
        {section:'Hip Activation'},{id:'hip_circle',reps:'10 each direction',note:'Slow circles. Wake up those hips.'},{id:'clamshell',sets:2,reps:'15 each side',note:'THE exercise for your hip. Squeeze the side of your hip.'},{id:'band_walk',sets:2,reps:'10 each direction',note:'Burn on the side of the hip = glute med working.'},
        {section:'Strength'},{id:'goblet',sets:3,reps:'12',note:'Light dumbbell. Only as deep as hips allow.'},{id:'hip_thrust',sets:3,reps:'12',note:'Squeeze glutes 2 sec at top.'},{id:'db_bench',sets:3,reps:'10',note:'Light dumbbells. Feel chest and arms.'},{id:'db_row',sets:3,reps:'10 each',note:'Pull to hip. Toned, strong back.'},{id:'db_shoulder',sets:3,reps:'10',note:'Seated. Light.'},
        {section:'Hip Cool Down'},{id:'pigeon',hold:'30s each',note:'Breathe into it. Massage gun on piriformis 1-2 min before this if you have one.'},{id:'figure4',hold:'30s each',note:'Gentle pull. Deep hip stretch.'},{id:'hip_flexor',hold:'30s each',note:'Open those hip flexors.'}
      ]},
      s_cardio:{name:'Cardio + Stretch',focus:'Your Choice of Machine',dur:'35 min',exercises:[
        {section:'Hip Warm-Up'},{id:'clamshell',sets:1,reps:'12 each',note:'Quick activation.'},{id:'hip_circle',reps:'10 each',note:'Loosen up.'},
        {section:'Cardio'},{id:'stair_ss',duration:'25 min',protocol:'Steady pace, RPE 5 \u2014 you can talk easily the whole time',note:'Pick ANY machine: stair stepper, elliptical, or bike. Whichever you enjoy. This is NOT supposed to hurt. Find a pace you could hold a conversation at.'},
        {section:'Stretch'},{id:'pigeon',hold:'45s each',note:'Extra long. Sink in.'},{id:'figure4',hold:'45s each',note:'Deep hip stretch.'},{id:'hip_flexor',hold:'45s each',note:'Open up.'},{id:'cat_cow',reps:'10 breaths',note:'Spine flow.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'},{id:'quad_str',hold:'30s each',note:'Quads.'}
      ]},
      s_full_b:{name:'Strength + Core',focus:'Full Body \u00b7 Home or Gym',dur:'40 min',exercises:[
        {section:'Hip Activation'},{id:'clamshell',sets:2,reps:'15 each',note:'Activate.'},{id:'fire_hydrant',sets:2,reps:'10 each',note:'Hip mobility + glute med.'},
        {section:'Strength'},{id:'trap_dl',sets:3,reps:'10',note:'Light. Hip hinge \u2014 the most functional movement. Flat back.'},{id:'db_lunge',sets:3,reps:'10 each',note:'Reverse lunges. Bodyweight fine to start.'},{id:'sl_bridge',sets:3,reps:'10 each',note:'Hip stability builder. Both legs if needed.'},{id:'pushup',sets:3,reps:'8-10',note:'Modified is perfect. No shame ever.'},{id:'db_curl',sets:2,reps:'12',note:'Light. Full range.'},{id:'tri_kick',sets:2,reps:'12 each',note:'Back of arm toning.'},
        {section:'Core'},{id:'plank',sets:3,reps:'30 seconds',note:'Hold strong. Knees OK.'},{id:'dead_bug',sets:3,reps:'10 each',note:'Press lower back to floor.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hip opener.'},{id:'cat_cow',reps:'8 breaths',note:'Spine release.'}
      ]},
      s_cardio2:{name:'Cardio Variety',focus:'Two Machines',dur:'35 min',exercises:[
        {section:'Hip Warm-Up'},{id:'clamshell',sets:1,reps:'12 each',note:'Activate.'},
        {section:'Cardio'},{id:'elliptical',duration:'20 min',protocol:'Moderate, alternate forward/backward every 5 min',note:'Forward = quads, backward = glutes. Low impact.'},{id:'bike',duration:'15 min',protocol:'Easy to moderate, change resistance every 3 min',note:'Finish on the bike. Easy on joints.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'hip_flexor',hold:'30s each',note:'Open up.'},{id:'cat_cow',reps:'8 breaths',note:'Spine.'}
      ]}
    }
  },
  {id:2,name:'Kindle',tag:'Fanning the flame',weeks:4,cardioDays:3,toneDays:1,
    desc:'Four days. Cardio variety increases. Strength feels easier \u2014 that means you\'re getting stronger. Hip exercises move to warm-up only \u2014 your hips are responding!',
    prog:'Cardio: 30 min. Strength: slightly more reps or weight. Hip: warm-up activation only.',
    schedule:[{type:'cardio',wk:'k_cardio'},{type:'tone',wk:'k_full_a'},{type:'rest'},{type:'cardio',wk:'k_cardio2'},{type:'cardio',wk:'s_cardio'},{type:'rest'},{type:'rest'}],
    workouts:{
      k_full_a:{name:'Strength',focus:'Full Body \u00b7 Gym',dur:'40 min',exercises:[
        {section:'Hip Warm-Up'},{id:'clamshell',sets:1,reps:'12 each',note:'Activate.'},{id:'band_walk',sets:1,reps:'10 each',note:'Glute med.'},
        {section:'Strength'},{id:'goblet',sets:3,reps:'12',note:'A little heavier if last time felt easy.'},{id:'hip_thrust',sets:3,reps:'15',note:'More reps. Squeeze every one.'},{id:'db_bench',sets:3,reps:'10',note:'Getting stronger.'},{id:'db_row',sets:3,reps:'10 each',note:'Pull to hip.'},{id:'db_shoulder',sets:3,reps:'10',note:'Controlled.'},{id:'lat_raise',sets:2,reps:'12',note:'Light. Shapes the shoulders.'},
        {section:'Core'},{id:'bird_dog',sets:3,reps:'10 each',note:'Balance.'},{id:'side_plank',sets:2,reps:'20s each',note:'From knees is great.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'hip_flexor',hold:'30s each',note:'Open up.'}
      ]},
      k_cardio:{name:'Cardio + Stretch',focus:'30 Min \u00b7 Machine Choice',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'stair_ss',duration:'30 min',protocol:'Steady RPE 5-6. Switch machines at 15 min if you want variety.',note:'Any machine. At 15 min, try switching to a different one for variety. Keeps it interesting.'},
        {section:'Extended Stretch'},{id:'pigeon',hold:'60s each',note:'Massage gun on piriformis first if you have one.'},{id:'figure4',hold:'60s each',note:'Relax.'},{id:'hip_flexor',hold:'60s each',note:'Open up.'},{id:'cat_cow',reps:'10 breaths',note:'Spine flow.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'}
      ]},
      k_full_b:{name:'Strength + Core',focus:'Full Body \u00b7 Home or Gym',dur:'40 min',exercises:[
        {section:'Hip Warm-Up'},{id:'clamshell',sets:1,reps:'12 each',note:'Activate.'},{id:'hip_circle',reps:'10 each',note:'Loosen.'},
        {section:'Strength'},{id:'trap_dl',sets:3,reps:'10',note:'Flat back, drive through feet.'},{id:'db_lunge',sets:3,reps:'10 each',note:'A bit heavier if ready.'},{id:'sl_bridge',sets:3,reps:'12 each',note:'Building hip stability.'},{id:'pushup',sets:3,reps:'10',note:'Try a few from toes if strong.'},{id:'db_curl',sets:2,reps:'12',note:'Arms.'},{id:'tri_kick',sets:2,reps:'12 each',note:'Back of arms.'},
        {section:'Core'},{id:'plank',sets:3,reps:'40s',note:'Longer!'},{id:'bike_crunch',sets:3,reps:'10 each',note:'Slow.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'cat_cow',reps:'8 breaths',note:'Spine.'}
      ]},
      k_cardio2:{name:'Incline Walk + Stretch',focus:'Treadmill Intervals',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'tread_inc',duration:'25 min',protocol:'3.0 mph: 2 min at 6% / 2 min at 2%, alternate',note:'ALWAYS interval the incline. This prevents shin pain.'},{id:'bike',duration:'10 min',protocol:'Easy cool down',note:'Easy finish.'},
        {section:'Stretch'},{id:'pigeon',hold:'45s each',note:'Hips.'},{id:'figure4',hold:'45s each',note:'Deep stretch.'},{id:'hip_flexor',hold:'45s each',note:'Open up.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'}
      ]}
    }
  },

  // ========== BLOCK 2: BUILD (Wks 9-24) — 4 days ==========
  {id:3,name:'Ignite',tag:'Adding a spark',weeks:4,cardioDays:3,toneDays:1,
    desc:'Four days a week! A second cardio day joins the party. Your hips feel better, your body is changing, and you have more energy. Let\'s use it beautifully.',
    prog:'Cardio: 30 min with 5 min of gentle intervals at the end. Strength: upper/lower split.',
    schedule:[{type:'cardio',wk:'i_cardio1'},{type:'tone',wk:'i_upper'},{type:'rest'},{type:'cardio',wk:'i_cardio2'},{type:'cardio',wk:'e_cardio2'},{type:'rest'},{type:'rest'}],
    workouts:{
      i_upper:{name:'Upper Body',focus:'Arms, Shoulders, Back, Core',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},{id:'cat_cow',reps:'8 breaths',note:'Spine.'},
        {section:'Upper Body'},{id:'db_bench',sets:3,reps:'10',note:'Chest and arms.'},{id:'db_row',sets:3,reps:'10 each',note:'Strong back.'},{id:'db_shoulder',sets:3,reps:'10',note:'Shoulders.'},{id:'pushup',sets:3,reps:'10-12',note:'Getting so good at these.'},{id:'lat_raise',sets:3,reps:'12',note:'Shoulder definition.'},{id:'db_curl',sets:2,reps:'12',note:'Arms.'},{id:'tri_kick',sets:2,reps:'12 each',note:'Toned arms.'},
        {section:'Core'},{id:'plank',sets:3,reps:'45s',note:'Hold strong.'},{id:'dead_bug',sets:3,reps:'10 each',note:'Core stability.'},{id:'side_plank',sets:2,reps:'25s each',note:'Obliques.'},
        {section:'Cool Down'},{id:'cat_cow',reps:'8 breaths',note:'Spine release.'}
      ]},
      i_cardio1:{name:'Cardio + Intervals',focus:'Stair Stepper or Incline',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'stair_int',duration:'30 min',protocol:'25 min steady (RPE 5) + 5 min intervals (1 min harder / 1 min easy)',note:'Mostly steady. Just 5 min of gentle intervals at the end. "Harder" means brisk, not dying.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'hip_flexor',hold:'30s each',note:'Open up.'}
      ]},
      i_lower:{name:'Lower Body + Hip Care',focus:'Legs, Glutes, Hips',dur:'40 min',exercises:[
        {section:'Hip Warm-Up'},{id:'clamshell',sets:1,reps:'12 each',note:'Activate.'},{id:'band_walk',sets:1,reps:'10 each',note:'Glute med.'},
        {section:'Lower Body'},{id:'goblet',sets:3,reps:'12',note:'Depth over weight.'},{id:'hip_thrust',sets:3,reps:'15',note:'Squeeze at top.'},{id:'db_lunge',sets:3,reps:'10 each',note:'Reverse lunges.'},{id:'sl_bridge',sets:3,reps:'10 each',note:'Hip stability.'},
        {section:'Stretch'},{id:'pigeon',hold:'45s each',note:'Deep hip opener.'},{id:'figure4',hold:'45s each',note:'Piriformis.'},{id:'hip_flexor',hold:'45s each',note:'Open.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'},{id:'quad_str',hold:'30s each',note:'Quads.'}
      ]},
      i_cardio2:{name:'Cardio Variety',focus:'Two Machines \u00b7 Steady',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'elliptical',duration:'20 min',protocol:'Moderate, alternate forward/backward every 5 min',note:'Forward = quads, backward = glutes.'},{id:'bike',duration:'15 min',protocol:'Easy to moderate, change resistance every 3 min',note:'Finish on the bike. Easy on your joints.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'cat_cow',reps:'8 breaths',note:'Spine.'}
      ]}
    }
  },
  {id:4,name:'Energize',tag:'Feeling the change',weeks:4,cardioDays:4,toneDays:1,
    desc:'Your body is different now. Clothes fit differently. You have energy you haven\'t felt in years. Cardio gets a few more minutes and slightly more intervals.',
    prog:'Cardio: 35 min with 8 min intervals. Introduce machine circuits.',
    schedule:[{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'e_cardio2'},{type:'tone',wk:'i_upper'},{type:'rest'},{type:'cardio',wk:'i_cardio1'},{type:'cardio',wk:'r_row'},{type:'rest'}],
    workouts:{
      e_cardio1:{name:'Cardio + Intervals',focus:'Stair Stepper or Incline',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'stair_int',duration:'35 min',protocol:'27 min steady (RPE 5-6) + 8 min intervals (1 min harder / 1 min easy)',note:'Little more time, little more intervals. The harder parts should feel challenging but totally doable. NOT gasping.'},
        {section:'Core'},{id:'plank',sets:3,reps:'45s',note:'Finish strong.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'}
      ]},
      e_cardio2:{name:'Machine Circuit',focus:'Rotate Every 12 Min',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio Circuit'},{id:'stair_ss',duration:'12 min',protocol:'Steady RPE 5-6',note:'First machine.'},{id:'elliptical',duration:'12 min',protocol:'Moderate, mix forward/backward',note:'Switch! Different muscles.'},{id:'bike',duration:'12 min',protocol:'Alternate moderate/easy every 3 min',note:'Third machine. Cool down on this one.'},
        {section:'Cool Down'},{id:'hip_flexor',hold:'30s each',note:'Open up.'},{id:'cat_cow',reps:'8 breaths',note:'Spine.'}
      ]}
    }
  },
  {id:5,name:'Rise',tag:'Watch yourself rise',weeks:4,cardioDays:4,toneDays:1,
    desc:'People are noticing. Comments are coming. The mirror tells a beautiful new story. Introduce rowing if you haven\'t tried it.',
    prog:'Cardio: 35-40 min. Rowing introduced. Strength: maintaining your tone.',
    schedule:[{type:'cardio',wk:'e_cardio2'},{type:'cardio',wk:'r_row'},{type:'tone',wk:'i_lower'},{type:'rest'},{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],
    workouts:{
      r_row:{name:'Row + Elliptical',focus:'Full Body Cardio',dur:'40 min',exercises:[
        {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
        {section:'Cardio'},{id:'rower',duration:'20 min',protocol:'Steady RPE 5-6, focus on leg drive',note:'Drive with legs first! If you haven\'t tried rowing, today is the day. Amazing full-body workout.'},{id:'elliptical',duration:'20 min',protocol:'Moderate, alternate directions every 5 min',note:'Low impact finish.'},
        {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'}
      ]}
    }
  },
  {id:6,name:'Empower',tag:'Own your strength',weeks:4,cardioDays:4,toneDays:1,
    desc:'Peak of the 4-day phase. You are strong, confident, and moving through the world differently. This is empowerment.',
    prog:'Cardio: 40 min. Intervals: 10-12 min. You are powerful.',
    schedule:[{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'s_cardio'},{type:'tone',wk:'i_upper'},{type:'rest'},{type:'cardio',wk:'r_row'},{type:'cardio',wk:'e_cardio2'},{type:'rest'}],workouts:{}
  },

  // ========== BLOCK 3: TRANSFORM (Wks 25-36) — 4-5 days ==========
  {id:7,name:'Transform',tag:'Becoming',weeks:4,cardioDays:4,toneDays:1,
    desc:'Optional 5th day appears \u2014 a light cardio + stretch session whenever you feel like it. No pressure, no guilt. You\'re in the groove.',
    prog:'5 days now — 4 cardio + 1 tone (walk/bike + stretch). Cardio: 40 min.',
    schedule:[{type:'cardio',wk:'r_row'},{type:'cardio',wk:'e_cardio1'},{type:'tone',wk:'i_lower'},{type:'rest'},{type:'cardio',wk:'e_cardio2'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],workouts:{}
  },
  {id:8,name:'Elevate',tag:'Rising higher',weeks:4,cardioDays:4,toneDays:1,
    desc:'You don\'t recognize old photos. The woman in the mirror is strong, energized, and radiant. Keep going.',
    prog:'5 days: 4 cardio + 1 tone. Peak cardio volume. 40-45 min sessions.',
    schedule:[{type:'cardio',wk:'e_cardio2'},{type:'cardio',wk:'s_cardio'},{type:'tone',wk:'i_upper'},{type:'rest'},{type:'cardio',wk:'r_row'},{type:'cardio',wk:'e_cardio1'},{type:'rest'}],workouts:{}
  },
  {id:9,name:'Shine',tag:'Let the world see',weeks:4,cardioDays:4,toneDays:1,
    desc:'You shine. Not because of any number \u2014 because YOU are different. Stronger. More alive.',
    prog:'5 days: 4 cardio, 1 tone. Peak variety. Your body adapts to nothing because we change everything.',
    schedule:[{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'r_row'},{type:'tone',wk:'i_lower'},{type:'rest'},{type:'cardio',wk:'e_cardio2'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],workouts:{}
  },

  // ========== BLOCK 4: SUSTAIN (Wks 37-48) — 4 days ==========
  {id:10,name:'Glow',tag:'You\'re glowing',weeks:4,cardioDays:4,toneDays:2,
    desc:'People ask what you\'re doing. The answer: you showed up, 3 or 4 days a week, for months. That\'s the secret.',
    prog:'6 days now. 4 cardio + 2 tone. You are a machine.',
    schedule:[{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'r_row'},{type:'cardio',wk:'e_cardio2'},{type:'tone',wk:'i_upper'},{type:'cardio',wk:'s_cardio'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],workouts:{}
  },
  {id:11,name:'Flourish',tag:'Thriving beautifully',weeks:4,cardioDays:5,toneDays:1,
    desc:'You are flourishing. Not just surviving \u2014 thriving. Your body is strong. Your mind is clear. This is who you\'ve always been.',
    prog:'6 days. This is peak you. Cardio you love, strength that keeps you toned.',
    schedule:[{type:'cardio',wk:'e_cardio2'},{type:'cardio',wk:'s_cardio'},{type:'cardio',wk:'r_row'},{type:'tone',wk:'i_lower'},{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],workouts:{}
  },
  {id:12,name:'Radiance',tag:'This is you',weeks:4,cardioDays:5,toneDays:1,
    desc:'This isn\'t an ending \u2014 it\'s a beginning. You\'ve built habits that will last forever. You are radiant. You are powerful. You are proof that showing up changes everything.',
    prog:'6 glorious days. Your sustainable peak. Cardio you enjoy. Strength that keeps you toned. You never have to go back.',
    schedule:[{type:'cardio',wk:'r_row'},{type:'cardio',wk:'e_cardio1'},{type:'cardio',wk:'e_cardio2'},{type:'tone',wk:'i_upper'},{type:'cardio',wk:'s_cardio'},{type:'cardio',wk:'s_cardio2'},{type:'rest'}],workouts:{}
  }
];
(function(){ var w=1; PHASES.forEach(function(p){ p.startWeek=w; w+=p.weeks; }); })();

// ---- NUTRITION ----
var NOURISH = {
  dayFocus:{cardio:'Hydrate before and after. Include protein with your next meal \u2014 your muscles need it.',tone:'Protein helps muscles recover and stay toned. Make it the star of your plate today.',rest:'Rest days are when your body gets stronger. Nourish with colorful, protein-rich foods.'},
  meals:[
    {name:'Breakfast Ideas',note:'Start with protein. It keeps you satisfied and energized all day.',ex:['Greek yogurt parfait with berries and granola','Veggie egg white omelette with spinach','Protein smoothie: spinach, banana, protein powder, almond milk','2 eggs + slice of whole grain toast','Overnight oats with chia seeds and berries']},
    {name:'Lunch Ideas',note:'Protein first, then veggies, then a small grain.',ex:['Grilled chicken salad with colorful veggies','Turkey lettuce wraps with avocado','Lentil soup with a side salad','Tuna salad on whole grain bread','Chicken veggie stir fry over rice']},
    {name:'Dinner Ideas',note:'Satisfied, not stuffed. Protein + veggies is the formula.',ex:['Baked salmon with roasted vegetables','Lean ground turkey stir fry','Chicken breast with sweet potato and broccoli','Shrimp with zucchini noodles','Turkey meatballs with spaghetti squash']}
  ],
  snacks:[{old:'Chips',better:'Roasted chickpeas or hummus + veggies'},{old:'Crackers',better:'Rice cakes with almond butter'},{old:'Candy',better:'Frozen grapes or dark chocolate square'},{old:'Ice cream',better:'Frozen Greek yogurt bark'},{old:'Cookies',better:'Protein bites or protein bar'},{old:'Granola bar',better:'String cheese + almonds'},{old:'Sugary cereal',better:'Greek yogurt + berries + honey'},{old:'Soda',better:'Sparkling water with lemon'}],
  wellness:['Your body thrives on protein \u2014 include some with every meal and snack','Small, satisfying portions work beautifully. Listen to your body.','Staying hydrated helps you feel amazing \u2014 water bottle always','Colorful plates are happy plates \u2014 2-3 colors per meal','Ginger or peppermint tea are wonderful for settling your stomach','Every meal is a chance to nourish yourself \u2014 no guilt, just fuel for your glow','Protein keeps you satisfied between meals','Eating slowly helps you feel satisfied','Sleep is magic \u2014 7-8 hours helps everything'],
  hydration:['Aim for 80+ ounces daily \u2014 more on workout days','Keep a pretty water bottle visible always','Infused water: cucumber+mint, lemon+ginger, strawberry+basil','Herbal tea counts! Chamomile, peppermint, ginger','Full glass first thing every morning','Sparkling water is wonderful if plain is boring']
};
var MILESTONES = [{n:5,msg:'Five! You\'re building something beautiful.'},{n:10,msg:'Double digits! Your body is thanking you.'},{n:25,msg:'25 workouts. You are glowing.'},{n:50,msg:'FIFTY. You are unstoppable.'},{n:75,msg:'75 times you chose yourself. Incredible.'},{n:100,msg:'One hundred. You\'ve transformed your life.'},{n:150,msg:'150. This is who you are now.'},{n:200,msg:'200. Legendary.'}];

// ---- STATE ----
var S = {
  _p:'rad_',
  get:function(k){ try{return JSON.parse(localStorage.getItem(this._p+k))}catch(e){return null} },
  set:function(k,v){ localStorage.setItem(this._p+k,JSON.stringify(v)) },
  get startDate(){ var d=this.get('start'); return d?new Date(d):null; },
  set startDate(d){ this.set('start',d.toISOString()); },
  get completed(){ return this.get('done')||{}; },
  setDone:function(ds,v){ var c=this.completed; if(v)c[ds]=true; else delete c[ds]; this.set('done',c); },
  session:function(ds){ return this.get('s_'+ds)||{}; },
  saveSession:function(ds,d){ this.set('s_'+ds,d); }
};

// ---- UTILITIES ----
function ds(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function norm(d){ return new Date(d.getFullYear(),d.getMonth(),d.getDate()); }
function fmt(d){ var days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']; return days[d.getDay()]+', '+mo[d.getMonth()]+' '+d.getDate(); }
function weekStart(d){ var day=d.getDay(); return norm(new Date(d.getFullYear(),d.getMonth(),d.getDate()+(day===0?-6:1-day))); }
function weekDates(off){ var s=weekStart(norm(new Date())); s.setDate(s.getDate()+off*7); return Array.from({length:7},function(_,i){var d=new Date(s);d.setDate(d.getDate()+i);return d;}); }
function phaseFor(date){ if(!S.startDate)return null; var diff=Math.round((norm(date)-norm(S.startDate))/864e5); if(diff<0)return null; var wk=Math.floor(diff/7)+1,cum=0; for(var i=0;i<PHASES.length;i++){var p=PHASES[i];if(wk<=cum+p.weeks)return{phase:p,wip:wk-cum,wk:wk};cum+=p.weeks;} return null; }
function workoutFor(date){ var pi=phaseFor(date); if(!pi)return null; var diff=Math.round((norm(date)-norm(S.startDate))/864e5),dayIdx=((diff%7)+7)%7,e=pi.phase.schedule[dayIdx]; if(!e||e.type==='rest')return{type:'rest',pi:pi}; var w=pi.phase.workouts?pi.phase.workouts[e.wk]:null; if(!w){for(var i=0;i<PHASES.length;i++){if(PHASES[i].workouts&&PHASES[i].workouts[e.wk]){w=PHASES[i].workouts[e.wk];break;}}} if(!w)return{type:'rest',pi:pi}; var r={}; for(var k in w)r[k]=w[k]; r.type=e.type; r.pi=pi; return r; }

// ---- PLANS ----
var Plans = {
  _key:'rad_plans',
  getAll:function(){ try{return JSON.parse(localStorage.getItem(this._key))||[];}catch(e){return[];} },
  save:function(name){ var plans=this.getAll(),data={};for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k.startsWith('rad_')&&k!==this._key)data[k]=localStorage.getItem(k);} var idx=plans.findIndex(function(p){return p.name===name;}); var plan={name:name,savedAt:new Date().toISOString(),data:data}; if(idx>=0)plans[idx]=plan;else plans.push(plan); localStorage.setItem(this._key,JSON.stringify(plans)); },
  load:function(name){ var plan=this.getAll().find(function(p){return p.name===name;}); if(!plan)return false; Object.keys(localStorage).filter(function(k){return k.startsWith('rad_')&&k!==Plans._key;}).forEach(function(k){localStorage.removeItem(k);}); for(var k in plan.data)localStorage.setItem(k,plan.data[k]); return true; },
  del:function(name){ localStorage.setItem(this._key,JSON.stringify(this.getAll().filter(function(p){return p.name!==name;}))); },
  reset:function(){ Object.keys(localStorage).filter(function(k){return k.startsWith('rad_')&&k!==Plans._key;}).forEach(function(k){localStorage.removeItem(k);}); }
};

// ---- APP ----
var App = {
  tab:'today', woff:0, ntab:'today',
  init:function(){
    var self=this;
    if(S.get('appver')!==APP_VERSION){ Plans.reset(); S.set('appver',APP_VERSION); }
    document.querySelectorAll('.tab').forEach(function(t){t.addEventListener('click',function(){self.tab=t.dataset.tab;self.woff=0;self.render();});});
    document.getElementById('menu-btn').addEventListener('click',function(){self.showPlansMenu();});
    this.render();
  },
  render:function(){
    var self=this;
    document.querySelectorAll('.tab').forEach(function(t){t.classList.toggle('active',t.dataset.tab===self.tab);});
    var b=document.getElementById('phase-badge');
    if(!S.startDate)b.textContent='BEGIN'; else{var pi=phaseFor(norm(new Date()));b.textContent=pi?pi.phase.name+' \u00b7 Wk '+pi.wip:'COMPLETE';}
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
    if(!S.startDate)return '<div class="setup"><h2><span class="accent">RADIANCE</span></h2><p class="sub">Your wellness journey starts here</p><div class="card"><p style="font-size:14px;color:var(--muted);line-height:1.7;margin-bottom:20px">A gentle, beautiful program that grows with you. Start with just 3 days a week. Every session includes hip care, feel-good cardio, and exercises that make you feel strong and confident.</p><div class="form-group"><label>When do you want to start?</label><input type="date" id="start-date" value="'+ds(today)+'"></div><button class="btn-primary" id="setup-btn">BEGIN YOUR JOURNEY</button></div></div>';
    if(today<norm(S.startDate))return '<div class="rest-hero"><h2>Your Journey Begins Soon</h2><p>Your program starts '+fmt(norm(S.startDate))+'. You\'re going to feel amazing.</p></div>';
    var w=workoutFor(today);
    if(!w)return '<div class="rest-hero"><h2>You Did It</h2><p>48 weeks. You showed up for yourself again and again. You are radiant.</p></div><div style="text-align:center;margin-top:16px"><button class="btn-secondary" id="reset-btn">Begin Again</button></div>';
    if(w.type==='rest')return '<div class="today-date">'+fmt(today)+'</div><div class="today-phase">'+w.pi.phase.name+' \u00b7 Week '+w.pi.wip+'</div><div class="rest-hero"><h2>Rest & Restore</h2><p>Your body gets stronger on rest days. Drink water, eat well, and do something that makes you smile.</p></div><div class="card"><div class="section-title">Rest Day Ideas</div><ul class="tip-list"><li>Gentle walk outside</li><li>10 min stretching</li><li>Massage gun on glutes and piriformis</li><li>Hydrate extra</li><li>7-8 hours of beautiful sleep</li></ul></div>';
    return this.rWorkout(w,today);
  },
  rWorkout:function(w,date){
    var d=ds(date),ses=S.session(d),done=S.completed[d];
    var h='<div class="today-date">'+fmt(date)+'</div><div class="today-phase">'+w.pi.phase.name+' \u00b7 Week '+w.pi.wip+'</div><div class="today-title">'+w.name+'</div><div class="today-focus '+(w.type==='cardio'?'cardio-focus':'tone-focus')+'">'+w.focus+' \u00b7 '+w.dur+'</div>';
    w.exercises.forEach(function(ex,i){
      if(ex.section){h+='<div class="section-marker">'+ex.section+'</div>';return;}
      var info=EX[ex.id]; if(!info)return;
      var sd=ses.sets&&ses.sets[i]||[];
      var isC=!!ex.duration,isH=!!ex.hold,n=ex.sets||1;
      var rx=isC?ex.duration:isH?ex.hold:(ex.sets?ex.sets+' \u00d7 '+ex.reps:ex.reps);
      h+='<div class="exercise"><div class="exercise-header"><span class="exercise-name" data-exid="'+ex.id+'">'+info.name+'</span><span class="exercise-rx'+(isC?' cardio-rx':'')+'">'+rx+'</span></div>';
      if(ex.protocol)h+='<div class="exercise-note" style="color:var(--cardio);font-weight:600">'+ex.protocol+'</div>';
      if(ex.note)h+='<div class="exercise-note">'+ex.note+'</div>';
      if(n===1||isC||isH){h+='<div class="sets-row"><button class="done-btn'+(sd[0]?' done':'')+'" data-idx="'+i+'" data-set="0">'+(sd[0]?'\u2713 Done':'Mark Done')+'</button></div>';}
      else{h+='<div class="sets-row">';for(var s=0;s<n;s++)h+='<button class="set-btn'+(sd[s]?' done':'')+'" data-idx="'+i+'" data-set="'+s+'">'+(s+1)+'</button>';h+='</div>';}
      h+='</div>';
    });
    h+='<button class="btn-complete'+(done?' completed':'')+'" id="complete-btn">'+(done?'COMPLETE \u2713':'COMPLETE WORKOUT')+'</button>';
    return h;
  },
  rCal:function(){
    var dates=weekDates(this.woff),today=ds(norm(new Date())),done=S.completed,dn=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    var s1=dates[0].toLocaleDateString('en',{month:'short',day:'numeric'}),s2=dates[6].toLocaleDateString('en',{month:'short',day:'numeric'});
    var h='<div class="week-nav"><button data-dir="-1">\u2190</button><span>'+s1+' \u2013 '+s2+'</span><button data-dir="1">\u2192</button></div>';
    dates.forEach(function(d,i){
      var dd=ds(d),w=S.startDate?workoutFor(d):null,isT=dd===today,isD=done[dd];
      var badge='',nm='',det='';
      if(!w||!S.startDate)nm='Not Started';
      else if(!phaseFor(d))nm='Journey Complete';
      else if(w.type==='rest'){nm='Rest & Restore';det='Recovery';}
      else if(w.type==='cardio'){badge='<span class="badge badge-cardio">CARDIO</span>';nm=w.name;det=w.focus;}
      else if(w.type==='tone'){badge='<span class="badge badge-tone">TONE</span>';nm=w.name;det=w.focus;}
      h+='<div class="day-card'+(isT?' today':'')+(isD?' completed':'')+'" data-date="'+dd+'"><div class="day-date"><div class="dow">'+dn[i]+'</div><div class="dom">'+d.getDate()+'</div></div><div class="day-info"><div class="dw">'+nm+' '+badge+'</div><div class="dd">'+det+'</div></div>'+(isD?'<div class="day-check">\u2713</div>':'')+'</div>';
    });
    return h;
  },
  rProg:function(){
    var pi=S.startDate?phaseFor(norm(new Date())):null,tot=PHASES.reduce(function(s,p){return s+p.weeks;},0);
    var cw=pi?pi.wk:(S.startDate?tot+1:0),pct=S.startDate?Math.min(cw/tot*100,100):0;
    var startDow=S.startDate?norm(S.startDate).getDay():3,dns=['Su','Mo','Tu','We','Th','Fr','Sa'];
    var dlab=Array.from({length:7},function(_,i){return dns[(startDow+i)%7];});
    var h='<div class="section-title">Your Journey</div><div class="progress-bar"><div class="progress-fill" style="width:'+pct+'%"></div></div><div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:20px"><span>Week '+Math.min(cw,tot)+' of '+tot+'</span><span>'+Math.round(pct)+'%</span></div>';
    PHASES.forEach(function(p){
      var cur=pi&&pi.phase.id===p.id,past=pi&&pi.phase.id>p.id,allDone=!pi&&S.startDate;
      h+='<div class="phase-card'+(cur?' current':'')+(past||allDone?' past':'')+'"><div class="phase-hdr"><span class="phase-name">'+p.name+'</span><span class="phase-wk">Wks '+p.startWeek+'\u2013'+(p.startWeek+p.weeks-1)+'</span></div><div class="phase-tag">'+p.tag+'</div><div class="phase-desc">'+p.desc+'</div><div class="phase-sched">'+p.schedule.map(function(e,idx){var t=e?e.type:'rest';return '<div class="phase-sched-day '+t+'"><div class="dl">'+dlab[idx]+'</div><div>'+(t==='cardio'?'C':t==='tone'?'T':'\u2013')+'</div></div>';}).join('')+'</div><div style="margin-top:8px;font-size:12px;color:var(--dim)">'+p.cardioDays+' cardio \u00b7 '+p.toneDays+' tone \u00b7 '+(7-p.cardioDays-p.toneDays)+' rest</div></div>';
    });
    if(S.startDate)h+='<div style="text-align:center;margin-top:20px"><button class="btn-secondary" id="reset-btn" style="color:var(--danger);border-color:var(--danger)">Reset Journey</button></div>';
    return h;
  },
  rNourish:function(){
    var self=this,today=norm(new Date()),w=S.startDate?workoutFor(today):null,dt=w?(w.type==='rest'?'rest':w.type):'rest';
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
      NOURISH.snacks.forEach(function(s){h+='<div class="snack-swap"><span class="snack-old">'+s.old+'</span><span class="snack-arrow">\u2192</span><span class="snack-new">'+s.better+'</span></div>';});
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
    var h='<div class="streak"><div class="streak-num">'+streak+'</div><div class="streak-lbl">Workout Streak</div></div>';
    h+='<div class="card" style="text-align:center"><div style="font-size:36px;font-weight:800;color:var(--primary)">'+total+'</div><div style="font-size:13px;color:var(--muted)">Workouts Completed</div></div>';
    if(aE>0)h+='<div class="card" style="text-align:center"><div class="section-title">This Week\'s Energy</div><div style="font-size:24px;font-weight:700;color:var(--primary)">'+aE+' / 5</div><div style="font-size:13px;color:var(--muted)">'+eL[Math.round(aE)]+'</div></div>';
    h+='<div class="card"><div class="section-title">Milestones</div>';
    MILESTONES.forEach(function(m){h+='<div class="milestone'+(total>=m.n?' reached':'')+'"><div class="milestone-num">'+m.n+'</div><div class="milestone-msg">'+(total>=m.n?m.msg:'Keep going...')+'</div></div>';});
    h+='</div>'; return h;
  },
  bindAll:function(){
    var self=this;
    document.querySelectorAll('.sub-tab').forEach(function(t){t.addEventListener('click',function(){self.ntab=t.dataset.st;self.render();});});
    document.querySelectorAll('.week-nav button').forEach(function(b){b.addEventListener('click',function(){self.woff+=parseInt(b.dataset.dir);self.render();});});
    var sb=document.getElementById('setup-btn');
    if(sb)sb.addEventListener('click',function(){var di=document.getElementById('start-date');if(!di||!di.value)return;var p=di.value.split('-');S.startDate=new Date(parseInt(p[0]),parseInt(p[1])-1,parseInt(p[2]));self.render();});
    var cb=document.getElementById('complete-btn');
    if(cb)cb.addEventListener('click',function(){var d=ds(norm(new Date())),wasDone=S.completed[d];S.setDone(d,!wasDone);if(!wasDone)self.showEnergy(d);else self.render();});
    document.querySelectorAll('.set-btn,.done-btn').forEach(function(b){b.addEventListener('click',function(){
      var idx=parseInt(b.dataset.idx),si=parseInt(b.dataset.set),d=ds(norm(new Date())),ses=S.session(d);
      if(!ses.sets)ses.sets={};if(!ses.sets[idx])ses.sets[idx]=[];
      while(ses.sets[idx].length<=si)ses.sets[idx].push(false);
      ses.sets[idx][si]=!ses.sets[idx][si];S.saveSession(d,ses);
      b.classList.toggle('done');
      if(b.classList.contains('done')){b.classList.add('pop');setTimeout(function(){b.classList.remove('pop');},300);if(b.classList.contains('done-btn'))b.textContent='\u2713 Done';}
      else{if(b.classList.contains('done-btn'))b.textContent='Mark Done';}
    });});
    document.querySelectorAll('.exercise-name').forEach(function(el){el.addEventListener('click',function(){self.showExInfo(el.dataset.exid);});});
    document.querySelectorAll('.day-card').forEach(function(c){c.addEventListener('click',function(){self.showDay(c.dataset.date);});});
    var rb=document.getElementById('reset-btn');
    if(rb)rb.addEventListener('click',function(){if(confirm('Start fresh? Saved plans are kept.')){Plans.reset();self.render();}});
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
    var cls={cardio:'cat-cardio',tone:'cat-tone',hip:'cat-hip',core:'cat-core',stretch:'cat-stretch'}[ex.cat]||'';
    var lbl={cardio:'Cardio',tone:'Toning',hip:'Hip Care',core:'Core',stretch:'Flexibility'}[ex.cat]||'';
    var ov=document.getElementById('overlay');ov.classList.remove('hidden');
    ov.innerHTML='<div class="overlay-content ex-info"><h3>'+ex.name+'</h3><span class="cat-tag '+cls+'">'+lbl+'</span> <a href="'+ex.yt+'" target="_blank" class="yt-link">\u25b6 Watch Demo</a>'+(ex.form?'<ol class="form-steps" style="margin-top:16px">'+ex.form.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ol>':'')+'<button class="close-btn" id="close-ov">Got it</button></div>';
    document.getElementById('close-ov').addEventListener('click',function(){ov.classList.add('hidden');});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.classList.add('hidden');});
  },
  showDay:function(dateStr){
    var parts=dateStr.split('-'),date=new Date(parseInt(parts[0]),parseInt(parts[1])-1,parseInt(parts[2]));
    var w=S.startDate?workoutFor(date):null;if(!w||w.type==='rest')return;
    var ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var c='<div class="overlay-content"><h3>'+w.name+'</h3><div style="font-size:13px;color:var(--muted);margin-bottom:12px">'+w.focus+' \u00b7 '+w.dur+'</div>';
    w.exercises.forEach(function(ex){if(ex.section){c+='<div class="section-marker">'+ex.section+'</div>';return;}var info=EX[ex.id];if(!info)return;var rx=ex.duration||ex.hold||(ex.sets?ex.sets+'\u00d7'+ex.reps:ex.reps);c+='<div style="padding:6px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between"><span style="font-weight:600;font-size:13px">'+info.name+'</span><span style="color:var(--muted);font-size:12px">'+rx+'</span></div>'+(ex.protocol?'<div style="font-size:11px;color:var(--cardio)">'+ex.protocol+'</div>':'')+'</div>';});
    c+='<button class="close-btn" id="close-ov">Close</button></div>';
    ov.innerHTML=c;
    document.getElementById('close-ov').addEventListener('click',function(){ov.classList.add('hidden');});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.classList.add('hidden');});
  },
  showPlansMenu:function(){
    var self=this,ov=document.getElementById('overlay');ov.classList.remove('hidden');
    var plans=Plans.getAll(),hasData=!!S.startDate,pi=hasData?phaseFor(norm(new Date())):null;
    var h='<div class="overlay-content"><h3 style="margin-bottom:16px">Plans</h3>';
    if(hasData)h+='<div class="section-title">Current</div><div style="font-size:13px;margin-bottom:12px">Started: '+fmt(norm(S.startDate))+'<br>'+(pi?pi.phase.name+' \u00b7 Week '+pi.wip:'Complete')+'</div>';
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
    document.querySelectorAll('.plan-btn-load').forEach(function(b){b.addEventListener('click',function(){if(confirm('Load "'+b.dataset.pn+'"?')){Plans.load(b.dataset.pn);closeOv();self.render();}});});
    document.querySelectorAll('.plan-btn-del').forEach(function(b){b.addEventListener('click',function(){if(confirm('Delete "'+b.dataset.pn+'"?')){Plans.del(b.dataset.pn);self.showPlansMenu();}});});
    document.getElementById('new-plan-btn').addEventListener('click',function(){if(!hasData||confirm('Start fresh?')){Plans.reset();closeOv();self.render();}});
  }
};
document.addEventListener('DOMContentLoaded',function(){App.init();});
