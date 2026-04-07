// ============================================================
// RADIANCE — 48-Week Women's Wellness Program
// Cardio + Toning + Hip Rehab + Nutrition Guidance
// ============================================================
const APP_VERSION = 1;

// ---- EXERCISE DATABASE ----
const EX = {
  // CARDIO
  stair_int:{name:'Stair Stepper Intervals',cat:'cardio',yt:'https://www.youtube.com/results?search_query=stair+stepper+interval+workout+beginner',
    form:['Start at a comfortable pace for 2-3 min to warm up','Increase speed or resistance for the "work" interval','Drop back to easy pace for recovery interval','Keep posture tall \u2014 light grip on rails, don\'t lean on them','Breathe rhythmically \u2014 in through nose, out through mouth']},
  stair_steady:{name:'Stair Stepper Steady',cat:'cardio',yt:'https://www.youtube.com/results?search_query=stair+stepper+workout+steady+state+fat+burn',
    form:['Find a pace you can maintain while breathing comfortably','Stand tall, light grip on rails','Engage your core \u2014 imagine pulling your belly button to your spine','Full steps \u2014 press through your whole foot']},
  tread_inc:{name:'Incline Treadmill Intervals',cat:'cardio',yt:'https://www.youtube.com/results?search_query=incline+treadmill+walking+workout+intervals',
    form:['Start flat for 2-3 min to warm up','Alternate between high incline and low incline every 2 min','Speed: 3.0-3.5 mph \u2014 brisk walk, never run','NEVER hold sustained max incline \u2014 always interval it','Light hand touch on rails only for balance if needed']},
  tread_hiit:{name:'Treadmill HIIT Walk',cat:'cardio',yt:'https://www.youtube.com/results?search_query=treadmill+hiit+walking+workout+fat+burn',
    form:['Alternate between fast walk (3.8-4.2 mph) and easy walk (2.5-3.0 mph)','30-60 seconds fast, 60-90 seconds easy','Keep incline at 1-3% for the HIIT portion','Hold the rails only if you need to for safety','This burns more than steady walking \u2014 the intervals are the magic']},
  elliptical:{name:'Elliptical',cat:'cardio',yt:'https://www.youtube.com/results?search_query=elliptical+workout+proper+form+beginner',
    form:['Stand tall, core engaged','Push and pull with arms \u2014 use the handles actively','Try both forward and backward pedaling (backward hits glutes more)','Moderate resistance \u2014 should feel challenging but sustainable','Great low-impact option that\'s easy on hips and knees']},
  bike:{name:'Stationary Bike',cat:'cardio',yt:'https://www.youtube.com/results?search_query=stationary+bike+workout+beginner+intervals',
    form:['Adjust seat height: slight bend in knee at bottom of pedal','Sit tall, relaxed shoulders','Alternate resistance levels for intervals','Easiest machine on your hips and joints','Great for days when things feel sore']},
  rower:{name:'Rowing Machine',cat:'cardio',yt:'https://www.youtube.com/results?search_query=rowing+machine+form+tutorial+beginner+woman',
    form:['Drive with LEGS first, then lean back, then pull arms','Return in reverse: arms, lean forward, bend knees','Keep core braced throughout','Don\'t pull with just your arms \u2014 80% of rowing is legs','Excellent full-body cardio \u2014 works everything']},

  // TONING
  goblet:{name:'Goblet Squat',cat:'tone',yt:'https://www.youtube.com/results?search_query=goblet+squat+form+women+beginner',
    form:['Hold a light dumbbell at your chest','Feet shoulder width, toes slightly out','Squat down keeping chest tall','Go as deep as comfortable \u2014 don\'t force depth if hips protest','Push through your whole foot to stand']},
  db_lunge:{name:'Dumbbell Lunge',cat:'tone',yt:'https://www.youtube.com/results?search_query=dumbbell+lunge+form+women',
    form:['Hold light dumbbells at your sides','Step forward, lower until both knees \u2248 90\u00b0','Keep front knee over ankle','Push back to start through front heel','If hips hurt, try shorter steps or reverse lunges instead']},
  glute_bridge:{name:'Glute Bridge',cat:'tone',yt:'https://www.youtube.com/results?search_query=glute+bridge+form+tutorial+women',
    form:['Lie on back, knees bent, feet flat on floor','Drive hips up by squeezing glutes HARD','Hold at top for 1-2 seconds','Lower with control','This is one of the best exercises for your glutes and hip health']},
  step_up:{name:'Step Up',cat:'tone',yt:'https://www.youtube.com/results?search_query=dumbbell+step+up+form+women',
    form:['Face a bench or sturdy step','Step up with one foot, drive through that heel','Stand fully on top','Step down with control','Use light dumbbells at sides or bodyweight']},
  wall_sit:{name:'Wall Sit',cat:'tone',yt:'https://www.youtube.com/results?search_query=wall+sit+proper+form+tutorial',
    form:['Back flat against wall, slide down until thighs parallel','Knees at 90\u00b0, directly over ankles','Hold the position \u2014 breathe!','Great for quad endurance without impact']},
  db_shoulder:{name:'Shoulder Press',cat:'tone',yt:'https://www.youtube.com/results?search_query=dumbbell+shoulder+press+form+women+light+weight',
    form:['Sit or stand with light dumbbells at shoulder height','Press straight up overhead','Lower with control back to shoulders','Keep core tight \u2014 don\'t arch your back','Go light \u2014 shoulders respond to form, not heavy weight']},
  db_row:{name:'Dumbbell Row',cat:'tone',yt:'https://www.youtube.com/results?search_query=one+arm+dumbbell+row+form+women',
    form:['One hand and knee on bench for support','Pull dumbbell to your hip with the other arm','Squeeze your shoulder blade at the top','Lower with control','Builds a strong, toned back']},
  pushup:{name:'Push-Up',cat:'tone',yt:'https://www.youtube.com/results?search_query=push+up+modified+form+women+beginner',
    form:['Start on knees (modified) or toes \u2014 both are great','Hands slightly wider than shoulders','Lower chest toward floor with control','Push back up','Modified is NOT easier \u2014 it\'s smarter. Work your way up.']},
  db_curl:{name:'Bicep Curl',cat:'tone',yt:'https://www.youtube.com/results?search_query=dumbbell+bicep+curl+form+women+toning',
    form:['Stand with light dumbbells, palms forward','Curl up, keeping elbows at your sides','Squeeze at the top, lower slowly','No swinging \u2014 slow and controlled wins']},
  tri_kick:{name:'Tricep Kickback',cat:'tone',yt:'https://www.youtube.com/results?search_query=tricep+kickback+form+women+toning',
    form:['Hinge forward slightly, elbow bent at 90\u00b0','Extend arm straight back, squeezing tricep','Return to 90\u00b0 with control','Light weight \u2014 you\'ll feel this quickly','Tones the back of the arm beautifully']},

  // HIP REHAB
  hip_circle:{name:'Hip Circles',cat:'hip',yt:'https://www.youtube.com/results?search_query=hip+circles+warm+up+mobility',
    form:['Stand on one leg (hold something for balance)','Make large circles with the other leg','10 circles forward, 10 backward, each leg','Warms up the hip joint and activates stabilizers']},
  clamshell:{name:'Clamshell',cat:'hip',yt:'https://www.youtube.com/results?search_query=clamshell+exercise+glute+medius+form',
    form:['Lie on side, knees bent at 45\u00b0, feet together','Open top knee like a clamshell, keeping feet touching','Squeeze your glute \u2014 you should feel it on the SIDE of your hip','Lower slowly','THIS is the #1 exercise for your hip pain \u2014 it strengthens the glute medius']},
  side_raise:{name:'Side-Lying Leg Raise',cat:'hip',yt:'https://www.youtube.com/results?search_query=side+lying+leg+raise+hip+abduction+form',
    form:['Lie on side, bottom leg bent for stability','Raise top leg straight up, leading with heel','Don\'t rotate hip forward \u2014 keep toes pointing forward or slightly down','Lower slowly','Targets the glute medius \u2014 the muscle that stabilizes your hip']},
  band_walk:{name:'Banded Lateral Walk',cat:'hip',yt:'https://www.youtube.com/results?search_query=banded+lateral+walk+glute+medius+form',
    form:['Place mini band just above knees (or ankles for harder)','Slight squat position, feet hip-width','Step sideways, keeping tension on the band','10 steps one way, 10 steps back','Keep your hips level \u2014 don\'t waddle']},
  fire_hydrant:{name:'Fire Hydrant',cat:'hip',yt:'https://www.youtube.com/results?search_query=fire+hydrant+exercise+glute+form+women',
    form:['On hands and knees, core tight','Lift one knee out to the side (like a dog at a fire hydrant)','Keep knee bent at 90\u00b0','Squeeze at the top, lower slowly','Great for hip mobility AND glute med strength']},
  sl_bridge:{name:'Single-Leg Glute Bridge',cat:'hip',yt:'https://www.youtube.com/results?search_query=single+leg+glute+bridge+form+tutorial',
    form:['Lie on back, one foot flat on floor, other leg extended up','Drive hips up using the grounded leg only','Squeeze glute hard at top','Lower with control','If too hard, start with regular glute bridges']},

  // CORE
  plank:{name:'Plank',cat:'core',yt:'https://www.youtube.com/results?search_query=plank+proper+form+women+beginner',
    form:['Forearms on floor, body in straight line from head to heels','Squeeze everything: glutes, core, quads','Don\'t let hips sag or pike up','Breathe! Don\'t hold your breath','On knees is a perfectly valid modification']},
  dead_bug:{name:'Dead Bug',cat:'core',yt:'https://www.youtube.com/results?search_query=dead+bug+exercise+form+tutorial+core',
    form:['Lie on back, arms straight up, knees bent 90\u00b0','Slowly extend opposite arm and leg toward floor','Keep lower back pressed into the floor \u2014 this is key','Return to start, switch sides','Gentle but incredibly effective for core stability']},
  bird_dog:{name:'Bird Dog',cat:'core',yt:'https://www.youtube.com/results?search_query=bird+dog+exercise+form+core+stability',
    form:['On hands and knees, core tight','Extend opposite arm and leg simultaneously','Hold for 1-2 seconds, return to start','Keep hips level \u2014 don\'t rotate','Builds core stability and balance']},
  side_plank:{name:'Side Plank',cat:'core',yt:'https://www.youtube.com/results?search_query=side+plank+form+women+beginner+modification',
    form:['Lie on side, forearm on floor, body in straight line','Lift hips off floor','Hold, breathing steadily','From knees is a great modification','Strengthens obliques and hip stabilizers']},
  bike_crunch:{name:'Bicycle Crunch',cat:'core',yt:'https://www.youtube.com/results?search_query=bicycle+crunch+proper+form+tutorial',
    form:['Lie on back, hands behind head','Bring opposite elbow to opposite knee','Extend the other leg straight','Alternate sides in a pedaling motion','Slow and controlled \u2014 no yanking on your neck']},

  // STRETCH
  pigeon:{name:'Pigeon Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=pigeon+stretch+hip+opener+beginner',
    form:['From hands and knees, bring one knee forward behind your wrist','Extend the other leg straight back','Sink hips toward the floor','Hold and breathe deeply','Amazing hip opener \u2014 targets the piriformis directly']},
  figure4:{name:'Figure-4 Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=figure+4+stretch+piriformis+hip',
    form:['Lie on back, cross one ankle over opposite knee','Pull the uncrossed leg toward your chest','You\'ll feel this deep in the crossed leg\'s hip/glute','Hold and breathe','Gentler alternative to pigeon \u2014 great for piriformis']},
  piriformis_str:{name:'Piriformis Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=seated+piriformis+stretch+sciatica+relief',
    form:['Sit in chair, cross one ankle over opposite knee','Lean forward gently with a straight back','Feel the stretch deep in your hip/glute','Hold 30 seconds each side','Do this multiple times a day if your hip is bothering you']},
  hip_flexor:{name:'Hip Flexor Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=hip+flexor+stretch+kneeling+form',
    form:['Kneel on one knee, other foot flat in front','Push hips forward gently','You\'ll feel the stretch in the front of the kneeling leg\'s hip','Keep torso tall','Tight hip flexors contribute to hip pain \u2014 this helps a lot']},
  cat_cow:{name:'Cat-Cow',cat:'stretch',yt:'https://www.youtube.com/results?search_query=cat+cow+stretch+spine+mobility',
    form:['On hands and knees','Arch back up (cat) \u2014 tuck chin, round spine','Then drop belly down (cow) \u2014 lift head, open chest','Flow between positions with your breath','Wonderful for spine mobility and stress relief']},
  quad_str:{name:'Quad Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=standing+quad+stretch+form',
    form:['Stand on one leg, grab the other foot behind you','Pull heel toward glute','Keep knees together','Hold something for balance if needed']},
  ham_str:{name:'Hamstring Stretch',cat:'stretch',yt:'https://www.youtube.com/results?search_query=standing+hamstring+stretch+form',
    form:['Place one heel on a low step or bench','Keep that leg straight, hinge forward at hips','Feel the stretch behind the knee and up the back of the leg','Don\'t round your back \u2014 hinge from the hips']}
};

// ---- PHASES (12 \u00d7 4 weeks = 48 weeks) ----
const PHASES = [
  // ========== BLOCK 1: FOUNDATION (Wks 1-12) ==========
  {id:1,name:'Spark',tag:'Light the Fire',weeks:4,cardioDays:2,toneDays:1,mode:'foundation',
    desc:'This is your beginning. Gentle cardio, hip rehab in every session, and light toning. The only goal: show up 3 times this week. That\'s it. You\'ve got this.',
    prog:'Hip rehab is the priority. Every warmup and cooldown includes hip exercises. Cardio stays easy and short. Toning uses light weight or bodyweight.',
    schedule:[
      {type:'cardio',wk:'p1_cardio1'},{type:'rest'},{type:'tone',wk:'p1_tone'},{type:'rest'},
      {type:'cardio',wk:'p1_cardio2'},{type:'rest'},{type:'rest'}
    ],
    workouts:{
      p1_cardio1:{name:'Cardio + Hip Care',focus:'Stair Stepper & Hip Activation',dur:'35 min',
        exercises:[
          {section:'Hip Activation'},
          {id:'hip_circle',reps:'10 each direction',note:'Warm up those hips. Slow circles, feel the joint move.'},
          {id:'clamshell',sets:2,reps:'15 each side',note:'THE exercise for your hip. Squeeze the glute on each rep.'},
          {id:'band_walk',sets:2,reps:'10 each direction',note:'Keep tension on the band. Feel the side of your hip working.'},
          {id:'fire_hydrant',sets:2,reps:'10 each side',note:'Slow and controlled. Squeeze at the top.'},
          {section:'Cardio'},
          {id:'stair_int',duration:'15 min',protocol:'2 min moderate / 1 min easy, repeat',note:'Find a comfortable rhythm. You should be able to talk during the easy parts.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each side',note:'Breathe into it. This directly targets the piriformis.'},
          {id:'figure4',hold:'30s each side',note:'Gentle pull. Feel the deep stretch in your hip.'},
          {id:'piriformis_str',hold:'30s each side',note:'Seated version. Great to do at home too.'},
          {id:'hip_flexor',hold:'30s each side',note:'Open up those hip flexors.'}
        ]},
      p1_tone:{name:'Full Body Tone + Hip Care',focus:'Light Weights & Glute Strength',dur:'35 min',
        exercises:[
          {section:'Hip Activation'},
          {id:'hip_circle',reps:'10 each direction',note:'Get those hips moving.'},
          {id:'clamshell',sets:2,reps:'15 each side',note:'Squeeze the glute. Slow reps.'},
          {id:'sl_bridge',sets:2,reps:'10 each side',note:'Drive through your heel. Single leg builds stability.'},
          {section:'Toning'},
          {id:'goblet',sets:3,reps:'15',note:'Light dumbbell. Focus on depth and control, not weight.'},
          {id:'db_lunge',sets:3,reps:'10 each leg',note:'If these bother your hip, try reverse lunges instead.'},
          {id:'glute_bridge',sets:3,reps:'15',note:'Squeeze at the top for 2 seconds each rep.'},
          {id:'db_shoulder',sets:3,reps:'12',note:'Light weight. Sit on a bench for stability.'},
          {id:'db_row',sets:3,reps:'12 each arm',note:'Pull to your hip. Squeeze your shoulder blade.'},
          {id:'pushup',sets:3,reps:'8-10',note:'Modified (from knees) is perfect. Quality over quantity.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each side',note:'Deep hip stretch.'},
          {id:'hip_flexor',hold:'30s each side',note:'Open the front of the hip.'},
          {id:'cat_cow',reps:'10 slow breaths',note:'Let your spine flow. Feels amazing.'}
        ]},
      p1_cardio2:{name:'Cardio Variety + Stretch',focus:'Easy Cardio & Flexibility',dur:'35 min',
        exercises:[
          {section:'Hip Activation'},
          {id:'hip_circle',reps:'10 each direction',note:'Quick warm-up.'},
          {id:'clamshell',sets:1,reps:'15 each side',note:'Wake up the glute med.'},
          {id:'band_walk',sets:1,reps:'10 each direction',note:'Feel the burn on the side of your hip.'},
          {section:'Cardio'},
          {id:'elliptical',duration:'12 min',protocol:'Moderate pace, mix forward and backward',note:'Low impact, full body. Backward pedaling targets your glutes more.'},
          {id:'bike',duration:'10 min',protocol:'Easy to moderate, change resistance every 2 min',note:'Easiest on your joints. Great active recovery option.'},
          {section:'Extended Stretch'},
          {id:'pigeon',hold:'45s each side',note:'Longer hold today. Sink into it.'},
          {id:'figure4',hold:'45s each side',note:'Breathe deeply and relax into the stretch.'},
          {id:'piriformis_str',hold:'30s each side',note:'Seated. Easy to do anywhere.'},
          {id:'hip_flexor',hold:'45s each side',note:'Really open those hip flexors.'},
          {id:'cat_cow',reps:'10 slow breaths',note:'Spine mobility. Flow with your breath.'},
          {id:'quad_str',hold:'30s each side',note:'Balance on one leg or hold the wall.'},
          {id:'ham_str',hold:'30s each side',note:'Hinge from hips, not back.'}
        ]}
    }
  },
  {id:2,name:'Kindle',tag:'Build the Flame',weeks:4,cardioDays:2,toneDays:1,mode:'foundation',
    desc:'You have the habit now. Time to add a little more intensity. Cardio gets longer, intervals get a bit harder, and toning starts to challenge you. Hip rehab moves to warmup only \u2014 your hips are getting stronger.',
    prog:'Cardio increases to 20 min. Stair stepper intervals get harder. Treadmill incline is introduced (always intervals \u2014 never sustained max incline). Toning adds core work.',
    schedule:[
      {type:'cardio',wk:'p2_cardio1'},{type:'rest'},{type:'tone',wk:'p2_tone'},{type:'rest'},
      {type:'cardio',wk:'p2_cardio2'},{type:'rest'},{type:'rest'}
    ],
    workouts:{
      p2_cardio1:{name:'Stair Stepper Power',focus:'Longer Intervals',dur:'35 min',
        exercises:[
          {section:'Hip Warm-Up'},
          {id:'clamshell',sets:1,reps:'12 each side',note:'Quick activation.'},
          {id:'band_walk',sets:1,reps:'10 each direction',note:'Wake up the glute med.'},
          {section:'Cardio'},
          {id:'stair_int',duration:'20 min',protocol:'2 min moderate / 1 min fast, repeat',note:'Bumped up to 20 min. Push a little harder on the fast intervals.'},
          {section:'Core'},
          {id:'plank',sets:3,reps:'30 seconds',note:'Hold strong. Breathe. Knees down is fine.'},
          {id:'dead_bug',sets:3,reps:'10 each side',note:'Slow and controlled. Press lower back into floor.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each side',note:'Hip opener.'},
          {id:'hip_flexor',hold:'30s each side',note:'Open the front of the hip.'}
        ]},
      p2_tone:{name:'Full Body Tone + Core',focus:'Toning & Stability',dur:'35 min',
        exercises:[
          {section:'Hip Warm-Up'},
          {id:'clamshell',sets:1,reps:'12 each side',note:'Quick glute med activation.'},
          {id:'hip_circle',reps:'10 each direction',note:'Loosen up.'},
          {section:'Toning'},
          {id:'goblet',sets:3,reps:'15',note:'Go a little heavier if the last set felt easy.'},
          {id:'db_lunge',sets:3,reps:'10 each leg',note:'Controlled steps. Reverse lunges if hips prefer.'},
          {id:'step_up',sets:3,reps:'10 each leg',note:'Drive through the top foot. Don\'t push off the floor.'},
          {id:'db_shoulder',sets:3,reps:'12',note:'Seated. Controlled.'},
          {id:'db_row',sets:3,reps:'12 each arm',note:'Pull to hip, squeeze blade.'},
          {id:'pushup',sets:3,reps:'10',note:'Try a few from toes if feeling strong.'},
          {id:'db_curl',sets:2,reps:'12',note:'Light weight, full range of motion.'},
          {id:'tri_kick',sets:2,reps:'12 each arm',note:'Squeeze the back of the arm.'},
          {section:'Core'},
          {id:'bird_dog',sets:3,reps:'10 each side',note:'Keep hips level. Don\'t rotate.'},
          {id:'side_plank',sets:2,reps:'20s each side',note:'From knees is great. Build up.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each side',note:'Breathe.'},
          {id:'cat_cow',reps:'8 breaths',note:'Spine feels great after this.'}
        ]},
      p2_cardio2:{name:'Incline Walk + Stretch',focus:'Treadmill Intervals & Flexibility',dur:'35 min',
        exercises:[
          {section:'Hip Warm-Up'},
          {id:'clamshell',sets:1,reps:'12 each side',note:'Quick activation.'},
          {section:'Cardio'},
          {id:'tread_inc',duration:'15 min',protocol:'3.0 mph: 2 min at 6% incline / 2 min at 2%, alternate',note:'ALWAYS interval the incline. Never hold max incline. This prevents shin pain.'},
          {id:'elliptical',duration:'10 min',protocol:'Moderate, mix forward/backward',note:'Easy finish to the cardio.'},
          {section:'Extended Stretch'},
          {id:'pigeon',hold:'45s each side',note:'Longer hold. Sink in.'},
          {id:'figure4',hold:'45s each side',note:'Deep hip stretch.'},
          {id:'hip_flexor',hold:'45s each side',note:'Open up.'},
          {id:'ham_str',hold:'30s each side',note:'Hamstrings.'},
          {id:'quad_str',hold:'30s each side',note:'Quads.'},
          {id:'cat_cow',reps:'10 breaths',note:'Finish with gentle spine work.'}
        ]}
    }
  },
  {id:3,name:'Ignite',tag:'4 Days Strong',weeks:4,cardioDays:2,toneDays:2,mode:'foundation',
    desc:'Welcome to 4 days a week! You\'re adding an extra training day. Cardio is getting longer and more challenging. Toning splits into upper and lower focus days. You\'re building real momentum.',
    prog:'Cardio: 25 min stair stepper, 18 min incline treadmill. Toning: split upper/lower for more focus per session. Core in every toning session.',
    schedule:[
      {type:'cardio',wk:'p3_cardio1'},{type:'tone',wk:'p3_upper'},{type:'rest'},
      {type:'cardio',wk:'p3_cardio2'},{type:'tone',wk:'p3_lower'},{type:'rest'},{type:'rest'}
    ],
    workouts:{
      p3_cardio1:{name:'Stair Stepper Challenge',focus:'25 Min Intervals',dur:'40 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},{id:'hip_circle',reps:'10 each',note:'Mobilize.'},
          {section:'Cardio'},
          {id:'stair_int',duration:'25 min',protocol:'2 min moderate / 1 min fast, repeat',note:'25 min! You\'ve come so far from 15. Push the fast intervals.'},
          {section:'Core'},
          {id:'plank',sets:3,reps:'40 seconds',note:'Getting stronger.'},
          {id:'bike_crunch',sets:3,reps:'12 each side',note:'Slow. Don\'t yank your neck.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each side',note:'Hip care.'},
          {id:'hip_flexor',hold:'30s each side',note:'Open up.'}
        ]},
      p3_upper:{name:'Upper Body + Core',focus:'Arms, Shoulders, Back',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},{id:'cat_cow',reps:'8 breaths',note:'Spine mobility.'},
          {section:'Upper Body'},
          {id:'db_shoulder',sets:3,reps:'12',note:'Seated, controlled.'},
          {id:'db_row',sets:3,reps:'12 each',note:'Squeeze at the top.'},
          {id:'pushup',sets:3,reps:'10-12',note:'Challenge yourself \u2014 try from toes.'},
          {id:'db_curl',sets:3,reps:'12',note:'Toning those arms.'},
          {id:'tri_kick',sets:3,reps:'12 each',note:'Back of the arm definition.'},
          {section:'Core'},
          {id:'dead_bug',sets:3,reps:'10 each',note:'Core stability.'},
          {id:'plank',sets:3,reps:'40s',note:'Hold strong.'},
          {id:'side_plank',sets:2,reps:'25s each',note:'Obliques and hip stability.'},
          {section:'Cool Down'},{id:'cat_cow',reps:'8 breaths',note:'Spine release.'}
        ]},
      p3_cardio2:{name:'Incline Power',focus:'Treadmill Intervals',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
          {section:'Cardio'},
          {id:'tread_inc',duration:'18 min',protocol:'3.2 mph: 2 min at 8% / 2 min at 3%, alternate',note:'Steeper incline now. Always interval it. Your shins are stronger.'},
          {id:'bike',duration:'10 min',protocol:'Moderate resistance intervals',note:'Low impact finish.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each',note:'Hip care.'},
          {id:'ham_str',hold:'30s each',note:'Hamstrings.'},
          {id:'hip_flexor',hold:'30s each',note:'Open up.'}
        ]},
      p3_lower:{name:'Lower Body + Stretch',focus:'Legs, Glutes & Flexibility',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},{id:'band_walk',sets:1,reps:'10 each',note:'Glute med.'},
          {section:'Lower Body'},
          {id:'goblet',sets:3,reps:'15',note:'Depth over weight.'},
          {id:'db_lunge',sets:3,reps:'10 each',note:'Controlled.'},
          {id:'glute_bridge',sets:3,reps:'15',note:'2 sec squeeze at top.'},
          {id:'step_up',sets:3,reps:'10 each',note:'Drive through top foot.'},
          {id:'wall_sit',sets:3,reps:'30 seconds',note:'Feel the quad burn.'},
          {section:'Extended Stretch'},
          {id:'pigeon',hold:'45s each',note:'Deep hip opener.'},
          {id:'figure4',hold:'45s each',note:'Piriformis relief.'},
          {id:'hip_flexor',hold:'45s each',note:'Open up.'},
          {id:'quad_str',hold:'30s each',note:'Quads.'},
          {id:'ham_str',hold:'30s each',note:'Hamstrings.'},
          {id:'cat_cow',reps:'10 breaths',note:'Spine flow.'}
        ]}
    }
  },

  // ========== BLOCK 2: BUILD (Wks 13-24) ==========
  {id:4,name:'Energize',tag:'Cardio Circuits',weeks:4,cardioDays:2,toneDays:2,mode:'build',
    desc:'New element: cardio circuits! Rotate between machines every 10 minutes to keep it fresh and prevent adaptation. HIIT treadmill is introduced. Your body is changing.',
    prog:'Cardio circuit: 10 min per machine, 3 machines. HIIT treadmill: 30s fast / 60s easy. Toning maintains with higher reps.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'rest'},
      {type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_recovery'},{type:'rest'},{type:'rest'}
    ],
    workouts:{
      p4_circuit:{name:'Cardio Circuit',focus:'Machine Rotation',dur:'40 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Quick glute activation.'},
          {section:'Cardio Circuit'},
          {id:'stair_int',duration:'10 min',protocol:'2 min moderate / 1 min fast',note:'First machine. Push the intervals.'},
          {id:'elliptical',duration:'10 min',protocol:'Moderate resistance, alternate forward/backward',note:'Switch machines! Different muscles, fresh energy.'},
          {id:'bike',duration:'10 min',protocol:'Resistance intervals: 1 min hard / 1 min easy',note:'Third machine. Finish strong.'},
          {section:'Core'},
          {id:'plank',sets:3,reps:'45s',note:'Getting stronger every week.'},
          {id:'dead_bug',sets:3,reps:'12 each',note:'Core stability.'},
          {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hip care.'},{id:'hip_flexor',hold:'30s each',note:'Open up.'}
        ]},
      p4_tone:{name:'Full Body Tone',focus:'Compound Movements',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
          {section:'Toning'},
          {id:'goblet',sets:3,reps:'15',note:'Go a little heavier if ready.'},
          {id:'db_lunge',sets:3,reps:'12 each',note:'More reps now. You can handle it.'},
          {id:'glute_bridge',sets:3,reps:'20',note:'High reps. Squeeze hard.'},
          {id:'db_shoulder',sets:3,reps:'12',note:'Controlled.'},
          {id:'db_row',sets:3,reps:'12 each',note:'Strong back.'},
          {id:'pushup',sets:3,reps:'12',note:'You\'re getting so much stronger at these.'},
          {id:'db_curl',sets:2,reps:'15',note:'Higher reps, feel the tone.'},
          {id:'tri_kick',sets:2,reps:'15 each',note:'Back of the arm.'},
          {section:'Core'},{id:'bird_dog',sets:3,reps:'10 each',note:'Stability.'},{id:'side_plank',sets:2,reps:'30s each',note:'Obliques.'},
          {section:'Cool Down'},{id:'cat_cow',reps:'8 breaths',note:'Spine release.'}
        ]},
      p4_hiit:{name:'HIIT Treadmill',focus:'Interval Walking',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Quick activation.'},
          {section:'Cardio'},
          {id:'tread_hiit',duration:'20 min',protocol:'30s fast (3.8-4.0 mph) / 60s easy (2.5 mph), repeat',note:'HIIT walking. The fast intervals should challenge you. This burns more than steady walking.'},
          {id:'stair_steady',duration:'10 min',protocol:'Moderate steady pace',note:'Steady state to finish.'},
          {section:'Cool Down'},
          {id:'pigeon',hold:'30s each',note:'Hip care.'},
          {id:'ham_str',hold:'30s each',note:'Hamstrings.'},
          {id:'hip_flexor',hold:'30s each',note:'Open up.'}
        ]},
      p4_recovery:{name:'Active Recovery',focus:'Gentle Movement & Stretch',dur:'30 min',
        exercises:[
          {section:'Easy Cardio'},
          {id:'bike',duration:'15 min',protocol:'Easy pace, very light resistance',note:'This is recovery. Keep it gentle and feel-good.'},
          {section:'Full Stretch'},
          {id:'pigeon',hold:'60s each',note:'Extra long hold. Sink deep.'},
          {id:'figure4',hold:'60s each',note:'Deep piriformis relief.'},
          {id:'hip_flexor',hold:'60s each',note:'Really open up.'},
          {id:'cat_cow',reps:'10 breaths',note:'Spine flow.'},
          {id:'quad_str',hold:'30s each',note:'Quads.'},
          {id:'ham_str',hold:'30s each',note:'Hamstrings.'}
        ]}
    }
  },
  {id:5,name:'Rise',tag:'Turning Up the Heat',weeks:4,cardioDays:2,toneDays:2,mode:'build',
    desc:'Cardio gets longer and more intense. HIIT intervals get harder. You are visibly different than when you started. Keep going \u2014 the transformation is happening.',
    prog:'Stair stepper: 25 min. HIIT treadmill: harder intervals. Toning: slightly heavier weights.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'rest'},
      {type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_recovery'},{type:'rest'},{type:'rest'}
    ],workouts:{}
  },
  {id:6,name:'Empower',tag:'Own Your Strength',weeks:4,cardioDays:2,toneDays:2,mode:'build',
    desc:'Peak of the 4-day block. Longest cardio sessions yet. You feel powerful. You\'re not just working out \u2014 you\'re choosing yourself every single day.',
    prog:'Cardio sessions hit 35 min. HIIT gets more rounds. Toning is maintenance \u2014 you\'re already strong.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'rest'},
      {type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_recovery'},{type:'rest'},{type:'rest'}
    ],workouts:{}
  },

  // ========== BLOCK 3: TRANSFORM (Wks 25-36) ==========
  {id:7,name:'Transform',tag:'5 Days',weeks:4,cardioDays:3,toneDays:2,mode:'transform',
    desc:'Five days a week! You\'re adding a third cardio day. Rowing machine enters the mix. You have more energy, more confidence, and more strength than you\'ve had in years.',
    prog:'Third cardio day: rower + elliptical combo. Other sessions maintain intensity. You\'re in a groove.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p7_rower'},
      {type:'rest'},{type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p3_lower'},{type:'rest'}
    ],
    workouts:{
      p7_rower:{name:'Row + Elliptical',focus:'Full Body Cardio',dur:'35 min',
        exercises:[
          {section:'Warm-Up'},{id:'clamshell',sets:1,reps:'10 each',note:'Activate.'},
          {section:'Cardio'},
          {id:'rower',duration:'15 min',protocol:'30s hard / 30s easy, repeat',note:'Rowing is full body. Drive with legs first, then pull. Amazing full-body workout.'},
          {id:'elliptical',duration:'15 min',protocol:'Moderate, alternate forward/backward every 3 min',note:'Low impact finish.'},
          {section:'Cool Down'},{id:'pigeon',hold:'30s each',note:'Hips.'},{id:'ham_str',hold:'30s each',note:'Hamstrings.'}
        ]}
    }
  },
  {id:8,name:'Elevate',tag:'Push Higher',weeks:4,cardioDays:3,toneDays:2,mode:'transform',
    desc:'Higher intensity across all sessions. Every workout leaves you feeling accomplished. You are not the same person who started this journey.',
    prog:'Longer intervals, more challenging circuits. Toning maintains your muscle while cardio sheds the rest.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p7_rower'},
      {type:'rest'},{type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p3_lower'},{type:'rest'}
    ],workouts:{}
  },
  {id:9,name:'Shine',tag:'Let It Show',weeks:4,cardioDays:3,toneDays:2,mode:'transform',
    desc:'Peak variety. Every session is different. You look forward to your workouts because they make you feel incredible. The changes in the mirror are undeniable.',
    prog:'Mix everything: circuits, HIIT, rowing, incline, steady state. Your body adapts to nothing because we change everything.',
    schedule:[
      {type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p7_rower'},
      {type:'rest'},{type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p3_lower'},{type:'rest'}
    ],workouts:{}
  },

  // ========== BLOCK 4: RADIATE (Wks 37-48) ==========
  {id:10,name:'Glow',tag:'You\'re Glowing',weeks:4,cardioDays:3,toneDays:2,mode:'radiate',
    desc:'People are noticing. Your energy is different. Your confidence is different. 5 days a week is your new normal. Keep shining.',
    prog:'Maintain peak fitness. Vary the cardio. Enjoy how strong and capable you feel.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p7_rower'},
      {type:'rest'},{type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_recovery'},{type:'rest'}
    ],workouts:{}
  },
  {id:11,name:'Flourish',tag:'Thriving',weeks:4,cardioDays:3,toneDays:2,mode:'radiate',
    desc:'You are thriving. Not just surviving \u2014 flourishing. Your body is strong, your mind is clear, your energy is boundless. This is who you are now.',
    prog:'Maintain everything. Challenge yourself with harder intervals when it feels right. You know your body.',
    schedule:[
      {type:'cardio',wk:'p4_hiit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p4_circuit'},
      {type:'rest'},{type:'cardio',wk:'p7_rower'},{type:'tone',wk:'p3_lower'},{type:'rest'}
    ],workouts:{}
  },
  {id:12,name:'Radiance',tag:'This Is You',weeks:4,cardioDays:3,toneDays:2,mode:'radiate',
    desc:'The final phase, but not the end. This is your new life. You\'ve built something that will last forever. You are radiant. You are powerful. You are proof that showing up changes everything.',
    prog:'You own this. Maintain, enjoy, and transition to a sustainable lifetime routine. You never have to go back.',
    schedule:[
      {type:'cardio',wk:'p4_circuit'},{type:'tone',wk:'p4_tone'},{type:'cardio',wk:'p4_hiit'},
      {type:'rest'},{type:'cardio',wk:'p7_rower'},{type:'tone',wk:'p4_recovery'},{type:'rest'}
    ],workouts:{}
  }
];
(function(){ let w=1; PHASES.forEach(p=>{ p.startWeek=w; w+=p.weeks; }); })();

// ---- NUTRITION (NO CALORIES, NO NUMBERS) ----
const NOURISH = {
  dayFocus:{
    cardio:'Hydrate well before and after your workout. Include protein with your next meal to help your body recover beautifully.',
    tone:'Protein helps your muscles stay toned and strong. Make it the star of your plate today.',
    rest:'Rest days are when your body gets stronger. Nourish yourself with colorful, protein-rich foods and plenty of water.'
  },
  meals:[
    {name:'Breakfast Ideas',note:'Start your day with protein to feel satisfied and energized.',
     ex:['Greek yogurt parfait with berries and a sprinkle of granola','Veggie egg white omelette with spinach and tomato','Protein smoothie: spinach, banana, protein powder, almond milk','2 eggs any style + slice of whole grain toast','Overnight oats with chia seeds, berries, and a drizzle of honey']},
    {name:'Lunch Ideas',note:'Build your plate: protein first, then veggies, then a small grain or starch.',
     ex:['Grilled chicken salad with lots of colorful veggies','Turkey lettuce wraps with avocado','Lentil soup with a side salad','Tuna salad on whole grain bread with mixed greens','Chicken + veggie stir fry over a small scoop of rice']},
    {name:'Dinner Ideas',note:'Your evening meal should leave you satisfied, not stuffed. Protein + veggies is the winning formula.',
     ex:['Baked salmon with roasted vegetables','Lean ground turkey stir fry with colorful peppers','Chicken breast with sweet potato and steamed broccoli','Shrimp with zucchini noodles and marinara','Turkey meatballs with spaghetti squash']}
  ],
  snacks:[
    {old:'Chips',better:'Roasted chickpeas or veggie chips with hummus'},
    {old:'Crackers',better:'Rice cakes with a thin layer of almond butter'},
    {old:'Candy',better:'Frozen grapes or a small square of dark chocolate'},
    {old:'Ice cream',better:'Frozen Greek yogurt bark with berries'},
    {old:'Cookies',better:'Protein bites or a protein bar'},
    {old:'Granola bar',better:'String cheese + a small handful of almonds'},
    {old:'Sugary cereal',better:'Plain Greek yogurt + berries + drizzle of honey'},
    {old:'Soda',better:'Sparkling water with lemon or cucumber'}
  ],
  wellness:[
    'Your body thrives on protein \u2014 include some with every meal and snack',
    'Small, satisfying portions work beautifully. Listen to your body\'s signals.',
    'Staying hydrated helps you feel your best \u2014 keep a water bottle with you always',
    'Colorful plates are happy plates \u2014 aim for 2-3 colors per meal',
    'Ginger tea or peppermint tea can help settle your stomach anytime',
    'Every meal is a chance to nourish yourself \u2014 no guilt, just fuel for your glow',
    'Protein keeps you satisfied longer \u2014 it\'s your secret weapon for feeling great',
    'Eating slowly helps you enjoy your food and feel satisfied',
    'Water before meals helps your body feel its best',
    'Sleep is magic \u2014 7-8 hours helps everything: energy, mood, recovery, and how you feel in your clothes'
  ],
  hydration:[
    'Aim for at least 80 ounces of water daily \u2014 more on workout days',
    'Keep a water bottle visible at all times as a gentle reminder',
    'Infused water ideas: cucumber + mint, lemon + ginger, strawberry + basil, orange + blueberry',
    'Herbal tea counts toward your water intake',
    'Drink a full glass of water first thing every morning \u2014 your body is dehydrated from sleep',
    'If plain water feels boring, sparkling water or flavored seltzer works great'
  ]
};

const MILESTONES = [
  {n:5,msg:'Five down! You\'re building something beautiful.'},
  {n:10,msg:'Double digits! Your body is thanking you.'},
  {n:25,msg:'25 workouts! You\'re absolutely glowing.'},
  {n:50,msg:'FIFTY. You are unstoppable.'},
  {n:75,msg:'75 sessions of choosing yourself. Incredible.'},
  {n:100,msg:'One hundred workouts. You\'ve transformed your life.'},
  {n:150,msg:'150. This isn\'t a phase \u2014 this is who you are.'},
  {n:200,msg:'200 workouts. Legendary.'}
];

// ---- STATE ----
const S = {
  _p:'rad_',
  get(k){ try{return JSON.parse(localStorage.getItem(this._p+k))}catch(e){return null} },
  set(k,v){ localStorage.setItem(this._p+k,JSON.stringify(v)) },
  get startDate(){ const d=this.get('start'); return d?new Date(d):null; },
  set startDate(d){ this.set('start',d.toISOString()); },
  get completed(){ return this.get('done')||{}; },
  setDone(ds,v){ const c=this.completed; if(v)c[ds]=true; else delete c[ds]; this.set('done',c); },
  session(ds){ return this.get('s_'+ds)||{}; },
  saveSession(ds,d){ this.set('s_'+ds,d); }
};

// ---- UTILITIES ----
function ds(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function norm(d){ return new Date(d.getFullYear(),d.getMonth(),d.getDate()); }
function fmt(d){ const days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']; const mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']; return days[d.getDay()]+', '+mo[d.getMonth()]+' '+d.getDate(); }
function weekStart(d){ const day=d.getDay(); return norm(new Date(d.getFullYear(),d.getMonth(),d.getDate()+(day===0?-6:1-day))); }
function weekDates(off){ const s=weekStart(norm(new Date())); s.setDate(s.getDate()+off*7); return Array.from({length:7},(_,i)=>{const d=new Date(s);d.setDate(d.getDate()+i);return d;}); }

function phaseFor(date){
  if(!S.startDate)return null;
  const diff=Math.round((norm(date)-norm(S.startDate))/864e5);
  if(diff<0)return null;
  const wk=Math.floor(diff/7)+1;
  let cum=0;
  for(const p of PHASES){ if(wk<=cum+p.weeks) return{phase:p,wip:wk-cum,wk:wk}; cum+=p.weeks; }
  return null;
}
function workoutFor(date){
  const pi=phaseFor(date); if(!pi)return null;
  const diff=Math.round((norm(date)-norm(S.startDate))/864e5);
  const dayIdx=((diff%7)+7)%7;
  const e=pi.phase.schedule[dayIdx];
  if(!e||e.type==='rest')return{type:'rest',pi};
  let w=pi.phase.workouts?pi.phase.workouts[e.wk]:null;
  if(!w) for(const p of PHASES){ if(p.workouts&&p.workouts[e.wk]){w=p.workouts[e.wk];break;} }
  if(!w) return{type:'rest',pi};
  return{...w,type:e.type,pi};
}

// ---- PLAN MANAGEMENT ----
const Plans = {
  _key:'rad_plans',
  getAll(){ try{return JSON.parse(localStorage.getItem(this._key))||[];}catch(e){return[];} },
  save(name){ const plans=this.getAll(),data={}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith('rad_')&&k!==this._key)data[k]=localStorage.getItem(k);} const idx=plans.findIndex(p=>p.name===name); const plan={name,savedAt:new Date().toISOString(),data}; if(idx>=0)plans[idx]=plan;else plans.push(plan); localStorage.setItem(this._key,JSON.stringify(plans)); },
  load(name){ const plan=this.getAll().find(p=>p.name===name); if(!plan)return false; Object.keys(localStorage).filter(k=>k.startsWith('rad_')&&k!==this._key).forEach(k=>localStorage.removeItem(k)); for(const[k,v]of Object.entries(plan.data))localStorage.setItem(k,v); return true; },
  del(name){ localStorage.setItem(this._key,JSON.stringify(this.getAll().filter(p=>p.name!==name))); },
  reset(){ Object.keys(localStorage).filter(k=>k.startsWith('rad_')&&k!==this._key).forEach(k=>localStorage.removeItem(k)); }
};

// ---- APP ----
const App = {
  tab:'today', woff:0, ntab:'today',

  init(){
    if(S.get('appver')!==APP_VERSION){ Plans.reset(); S.set('appver',APP_VERSION); }
    document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{
      this.tab=t.dataset.tab; this.woff=0; this.render();
    }));
    document.getElementById('menu-btn').addEventListener('click',()=>this.showPlansMenu());
    this.render();
  },

  render(){
    document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===this.tab));
    const b=document.getElementById('phase-badge');
    if(!S.startDate) b.textContent='BEGIN';
    else{ const pi=phaseFor(norm(new Date())); b.textContent=pi?`${pi.phase.name} \u00b7 Wk ${pi.wip}`:'COMPLETE'; }
    const el=document.getElementById('content');
    switch(this.tab){
      case'today':el.innerHTML=this.rToday();break;
      case'calendar':el.innerHTML=this.rCal();break;
      case'program':el.innerHTML=this.rProg();break;
      case'nourish':el.innerHTML=this.rNourish();break;
      case'journey':el.innerHTML=this.rJourney();break;
    }
    this.bindAll();
  },

  // ---- TODAY ----
  rToday(){
    const today=norm(new Date());
    if(!S.startDate) return this.rSetup();
    if(today<norm(S.startDate)) return'<div class="rest-hero"><h2>Your Journey Begins Soon</h2><p>Take a deep breath. Get excited. Your program starts '+fmt(norm(S.startDate))+'. You\'re going to feel amazing.</p></div>';
    const w=workoutFor(today);
    if(!w) return'<div class="rest-hero"><h2>You Did It</h2><p>48 weeks. You showed up for yourself again and again. You are radiant. You are powerful. This is who you are now.</p></div><div style="text-align:center;margin-top:16px"><button class="btn-secondary" id="reset-btn">Begin a New Journey</button></div>';
    if(w.type==='rest') return this.rRest(today,w.pi);
    return this.rWorkout(w,today);
  },

  rSetup(){
    const def=ds(norm(new Date()));
    return'<div class="setup"><h2><span class="accent">RADIANCE</span></h2><p class="sub">Your wellness journey starts here</p><div class="card"><p style="font-size:13px;color:var(--muted);line-height:1.6;margin-bottom:20px">A personalized program that grows with you. Start with 3 days a week and build from there. Every workout includes hip care, feel-good cardio, and toning that makes you strong and confident.</p><div class="form-group"><label>When do you want to start?</label><input type="date" id="start-date" value="'+def+'"></div><button class="btn-primary" id="setup-btn">BEGIN YOUR JOURNEY</button></div></div>';
  },

  rRest(date,pi){
    return'<div class="today-date">'+fmt(date)+'</div><div class="today-phase">'+pi.phase.name+' \u00b7 Week '+pi.wip+'</div><div class="rest-hero"><h2>Rest & Restore</h2><p>Your body gets stronger on rest days. Drink plenty of water, eat protein-rich foods, and do something that makes you smile. You\'ve earned this.</p></div><div class="card"><div class="section-title">Rest Day Ideas</div><ul class="tip-list"><li>Gentle walk outside \u2014 fresh air is medicine</li><li>Stretch for 10 min \u2014 your hips will thank you</li><li>Hydrate extra \u2014 your body is recovering</li><li>Nourish yourself with colorful, protein-rich meals</li><li>Get 7-8 hours of sleep tonight</li></ul></div>';
  },

  rWorkout(w,date){
    const d=ds(date),ses=S.session(d),done=S.completed[d];
    const typeClass=w.type==='cardio'?'cardio-focus':'tone-focus';
    const typeBadge=w.type==='cardio'?'badge-cardio':'badge-tone';
    let h='<div class="today-date">'+fmt(date)+'</div><div class="today-phase">'+w.pi.phase.name+' \u00b7 Week '+w.pi.wip+'</div><div class="today-title">'+w.name+'</div><div class="today-focus '+typeClass+'">'+w.focus+' \u00b7 '+w.dur+'</div>';

    w.exercises.forEach((ex,i)=>{
      if(ex.section){
        h+='<div class="section-marker">'+ex.section+'</div>';
        return;
      }
      const info=EX[ex.id];
      if(!info)return;
      const setsDone=ses.sets&&ses.sets[i]||[];
      const isCardio=!!ex.duration;
      const isHold=!!ex.hold;
      const numSets=ex.sets||1;
      const rx=isCardio?ex.duration:isHold?ex.hold:(ex.sets?ex.sets+' \u00d7 '+ex.reps:ex.reps);
      const rxClass=isCardio?'exercise-rx cardio-rx':'exercise-rx';

      h+='<div class="exercise"><div class="exercise-header"><span class="exercise-name" data-exid="'+ex.id+'">'+info.name+'</span><span class="'+rxClass+'">'+rx+'</span></div>';
      if(ex.protocol) h+='<div class="exercise-note" style="color:var(--cardio);font-weight:600">'+ex.protocol+'</div>';
      if(ex.note) h+='<div class="exercise-note">'+ex.note+'</div>';

      if(numSets===1||isCardio||isHold){
        h+='<div class="sets-row"><button class="done-btn'+(setsDone[0]?' done':'')+'" data-idx="'+i+'" data-set="0">'+(setsDone[0]?'\u2713 Done':'Mark Done')+'</button></div>';
      } else {
        h+='<div class="sets-row">';
        for(let s=0;s<numSets;s++) h+='<button class="set-btn'+(setsDone[s]?' done':'')+'" data-idx="'+i+'" data-set="'+s+'">'+(s+1)+'</button>';
        h+='</div>';
      }
      h+='</div>';
    });

    h+='<button class="btn-complete'+(done?' completed':'')+'" id="complete-btn">'+(done?'WORKOUT COMPLETE \u2713':'COMPLETE WORKOUT')+'</button>';
    return h;
  },

  // ---- CALENDAR ----
  rCal(){
    const dates=weekDates(this.woff),today=ds(norm(new Date())),done=S.completed;
    const dn=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    const s1=dates[0].toLocaleDateString('en',{month:'short',day:'numeric'});
    const s2=dates[6].toLocaleDateString('en',{month:'short',day:'numeric'});
    let h='<div class="week-nav"><button data-dir="-1">\u2190 Prev</button><span>'+s1+' \u2013 '+s2+'</span><button data-dir="1">Next \u2192</button></div>';
    dates.forEach((d,i)=>{
      const dd=ds(d),w=S.startDate?workoutFor(d):null,isT=dd===today,isD=done[dd];
      let badge='',nm='',det='';
      if(!w||!S.startDate){nm='Not Started';}
      else if(!phaseFor(d)){nm='Journey Complete';}
      else if(w.type==='rest'){nm='Rest & Restore';det='Recovery day';}
      else if(w.type==='cardio'){badge='<span class="badge badge-cardio">CARDIO</span>';nm=w.name;det=w.focus+' \u00b7 '+w.dur;}
      else if(w.type==='tone'){badge='<span class="badge badge-tone">TONE</span>';nm=w.name;det=w.focus+' \u00b7 '+w.dur;}
      h+='<div class="day-card'+(isT?' today':'')+(isD?' completed':'')+'" data-date="'+dd+'"><div class="day-date"><div class="dow">'+dn[i]+'</div><div class="dom">'+d.getDate()+'</div></div><div class="day-info"><div class="dw">'+nm+' '+badge+'</div><div class="dd">'+det+'</div></div>'+(isD?'<div class="day-check">\u2713</div>':'')+'</div>';
    });
    return h;
  },

  // ---- PROGRAM ----
  rProg(){
    const pi=S.startDate?phaseFor(norm(new Date())):null;
    const tot=PHASES.reduce((s,p)=>s+p.weeks,0);
    const cw=pi?pi.wk:(S.startDate?tot+1:0);
    const pct=S.startDate?Math.min(cw/tot*100,100):0;
    const startDow=S.startDate?norm(S.startDate).getDay():4;
    const dns=['Su','Mo','Tu','We','Th','Fr','Sa'];
    const dlab=Array.from({length:7},(_,i)=>dns[(startDow+i)%7]);
    let h='<div class="section-title">Your Journey</div><div class="progress-bar"><div class="progress-fill" style="width:'+pct+'%"></div></div><div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:20px"><span>Week '+Math.min(cw,tot)+' of '+tot+'</span><span>'+Math.round(pct)+'%</span></div>';
    PHASES.forEach(p=>{
      const cur=pi&&pi.phase.id===p.id,past=pi&&pi.phase.id>p.id,allDone=!pi&&S.startDate;
      h+='<div class="phase-card'+(cur?' current':'')+(past||allDone?' past':'')+'"><div class="phase-hdr"><span class="phase-name">'+p.name+'</span><span class="phase-wk">Wks '+p.startWeek+'\u2013'+(p.startWeek+p.weeks-1)+'</span></div><div class="phase-tag">'+p.tag+'</div><div class="phase-desc">'+p.desc+'</div><div class="phase-sched">'+p.schedule.map((e,idx)=>{const t=e?e.type:'rest';return'<div class="phase-sched-day '+t+'"><div class="dl">'+dlab[idx]+'</div><div>'+(t==='cardio'?'C':t==='tone'?'T':'\u2013')+'</div></div>';}).join('')+'</div><div style="margin-top:8px;font-size:12px;color:var(--dim)">'+p.cardioDays+' cardio \u00b7 '+p.toneDays+' tone \u00b7 '+(7-p.cardioDays-p.toneDays)+' rest</div></div>';
    });
    if(S.startDate)h+='<div style="text-align:center;margin-top:20px"><button class="btn-secondary" id="reset-btn" style="color:var(--danger);border-color:var(--danger)">Reset Journey</button></div>';
    return h;
  },

  // ---- NOURISH ----
  rNourish(){
    const today=norm(new Date()),w=S.startDate?workoutFor(today):null;
    const dayType=w?(w.type==='rest'?'rest':w.type):'rest';
    let h='<div class="sub-tabs"><button class="sub-tab'+(this.ntab==='today'?' active':'')+'" data-st="today">Today</button><button class="sub-tab'+(this.ntab==='meals'?' active':'')+'" data-st="meals">Meals</button><button class="sub-tab'+(this.ntab==='snacks'?' active':'')+'" data-st="snacks">Snacks</button><button class="sub-tab'+(this.ntab==='wellness'?' active':'')+'" data-st="wellness">Wellness</button></div>';

    if(this.ntab==='today'){
      const badge=dayType==='cardio'?'badge-cardio':dayType==='tone'?'badge-tone':'badge-rest';
      const label=dayType==='cardio'?'Cardio Day':dayType==='tone'?'Toning Day':'Rest Day';
      h+='<div class="card"><span class="badge '+badge+'">'+label+'</span><p style="font-size:14px;line-height:1.6;margin-top:12px">'+NOURISH.dayFocus[dayType]+'</p></div>';
      h+='<div class="card"><div class="section-title">Today\'s Focus</div><ul class="tip-list"><li>Start every meal with a protein source</li><li>Add 2-3 colorful vegetables to your plate</li><li>Drink a glass of water before each meal</li><li>Choose a smart snack if you get hungry between meals</li></ul></div>';
      h+='<div class="card"><div class="section-title">Hydration Reminder</div><ul class="tip-list">'+NOURISH.hydration.slice(0,3).map(t=>'<li>'+t+'</li>').join('')+'</ul></div>';
    }
    else if(this.ntab==='meals'){
      NOURISH.meals.forEach(m=>{
        h+='<div class="meal"><div class="meal-name">'+m.name+'</div><div class="meal-note">'+m.note+'</div><ul class="meal-examples">'+m.ex.map(e=>'<li>'+e+'</li>').join('')+'</ul></div>';
      });
    }
    else if(this.ntab==='snacks'){
      h+='<div class="card"><div class="section-title">Smart Swaps</div><p style="font-size:12px;color:var(--muted);margin-bottom:12px">Same satisfaction, better nourishment. Try swapping these:</p>';
      NOURISH.snacks.forEach(s=>{
        h+='<div class="snack-swap"><span class="snack-old">'+s.old+'</span><span class="snack-arrow">\u2192</span><span class="snack-new">'+s.better+'</span></div>';
      });
      h+='</div>';
    }
    else if(this.ntab==='wellness'){
      h+='<div class="card"><div class="section-title">Nourishing Your Radiance</div><ul class="tip-list">'+NOURISH.wellness.map(t=>'<li>'+t+'</li>').join('')+'</ul></div>';
      h+='<div class="card"><div class="section-title">Hydration</div><ul class="tip-list">'+NOURISH.hydration.map(t=>'<li>'+t+'</li>').join('')+'</ul></div>';
    }
    return h;
  },

  // ---- JOURNEY ----
  rJourney(){
    const done=S.completed,today=ds(norm(new Date()));
    // Total workouts
    const totalWorkouts=Object.keys(done).length;
    // Streak
    let streak=0;
    for(let i=0;i<200;i++){const d=new Date();d.setDate(d.getDate()-i);const dd=ds(norm(d)),w=S.startDate?workoutFor(norm(d)):null;if(w&&w.type&&w.type!=='rest'){if(done[dd])streak++;else if(i>0)break;}}
    // Energy average this week
    const weekD=weekDates(0);
    let energySum=0,energyCount=0;
    weekD.forEach(d=>{const ses=S.session(ds(d));if(ses.energy){energySum+=ses.energy;energyCount++;}});
    const avgEnergy=energyCount?Math.round(energySum/energyCount*10)/10:0;
    const energyLabels=['','Low','OK','Good','Great','Amazing'];

    let h='<div class="streak"><div class="streak-num">'+streak+'</div><div class="streak-lbl">Workout Streak</div></div>';
    h+='<div class="card" style="text-align:center"><div style="font-size:32px;font-weight:800;color:var(--primary)">'+totalWorkouts+'</div><div style="font-size:13px;color:var(--muted)">Total Workouts Completed</div></div>';

    // Energy this week
    if(avgEnergy>0){
      h+='<div class="card"><div class="section-title">This Week\'s Energy</div><div style="text-align:center;font-size:20px;font-weight:700;color:var(--primary)">'+avgEnergy+' / 5</div><div style="text-align:center;font-size:13px;color:var(--muted)">Average: '+energyLabels[Math.round(avgEnergy)]+'</div></div>';
    }

    // Milestones
    h+='<div class="card"><div class="section-title">Milestones</div>';
    MILESTONES.forEach(m=>{
      const reached=totalWorkouts>=m.n;
      h+='<div class="milestone'+(reached?' reached':'')+'"><div class="milestone-num">'+m.n+'</div><div class="milestone-msg">'+(reached?m.msg:'Keep going...')+'</div></div>';
    });
    h+='</div>';
    return h;
  },

  // ---- EVENT HANDLERS ----
  bindAll(){
    document.querySelectorAll('.sub-tab').forEach(t=>t.addEventListener('click',()=>{this.ntab=t.dataset.st;this.render();}));
    document.querySelectorAll('.week-nav button').forEach(b=>b.addEventListener('click',()=>{this.woff+=parseInt(b.dataset.dir);this.render();}));

    // Setup
    const sb=document.getElementById('setup-btn');
    if(sb)sb.addEventListener('click',()=>{
      const di=document.getElementById('start-date');
      if(!di||!di.value)return;
      const parts=di.value.split('-');S.startDate=new Date(parseInt(parts[0]),parseInt(parts[1])-1,parseInt(parts[2]));
      this.render();
    });

    // Complete workout
    const cb=document.getElementById('complete-btn');
    if(cb)cb.addEventListener('click',()=>{
      const d=ds(norm(new Date()));
      const wasDone=S.completed[d];
      S.setDone(d,!wasDone);
      // If just completed and no energy logged, show energy prompt
      if(!wasDone){ this.showEnergyPrompt(d); } else { this.render(); }
    });

    // Set/done buttons
    document.querySelectorAll('.set-btn,.done-btn').forEach(b=>b.addEventListener('click',()=>{
      const idx=parseInt(b.dataset.idx),si=parseInt(b.dataset.set),d=ds(norm(new Date())),ses=S.session(d);
      if(!ses.sets)ses.sets={};if(!ses.sets[idx])ses.sets[idx]=[];
      while(ses.sets[idx].length<=si)ses.sets[idx].push(false);
      ses.sets[idx][si]=!ses.sets[idx][si]; S.saveSession(d,ses);
      b.classList.toggle('done');
      if(b.classList.contains('done')){b.classList.add('pop');setTimeout(()=>b.classList.remove('pop'),300);
        if(b.classList.contains('done-btn'))b.textContent='\u2713 Done';
      } else { if(b.classList.contains('done-btn'))b.textContent='Mark Done'; }
    }));

    // Exercise info
    document.querySelectorAll('.exercise-name').forEach(el=>el.addEventListener('click',()=>this.showExInfo(el.dataset.exid)));
    // Calendar day
    document.querySelectorAll('.day-card').forEach(c=>c.addEventListener('click',()=>this.showDay(c.dataset.date)));
    // Reset
    const rb=document.getElementById('reset-btn');
    if(rb)rb.addEventListener('click',()=>{if(confirm('Start fresh? Saved plans are kept.')){Plans.reset();this.render();}});
  },

  // ---- ENERGY PROMPT ----
  showEnergyPrompt(dateStr){
    const ov=document.getElementById('overlay');ov.classList.remove('hidden');
    ov.innerHTML='<div class="overlay-content" style="text-align:center"><h3 style="margin-bottom:8px">How do you feel?</h3><p style="font-size:13px;color:var(--muted);margin-bottom:16px">Rate your energy after that workout</p><div class="energy-row"><button class="energy-btn" data-e="1">1</button><button class="energy-btn" data-e="2">2</button><button class="energy-btn" data-e="3">3</button><button class="energy-btn" data-e="4">4</button><button class="energy-btn" data-e="5">5</button></div><div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:16px"><span>Low</span><span>Amazing</span></div><button class="close-btn" id="skip-energy">Skip</button></div>';

    document.querySelectorAll('.energy-btn').forEach(b=>b.addEventListener('click',()=>{
      const ses=S.session(dateStr);ses.energy=parseInt(b.dataset.e);S.saveSession(dateStr,ses);
      ov.classList.add('hidden');this.render();
    }));
    document.getElementById('skip-energy').addEventListener('click',()=>{ov.classList.add('hidden');this.render();});
    ov.addEventListener('click',e=>{if(e.target===ov){ov.classList.add('hidden');this.render();}});
  },

  // ---- EXERCISE INFO ----
  showExInfo(id){
    const ex=EX[id];if(!ex)return;
    const catCls={cardio:'cat-cardio',tone:'cat-tone',hip:'cat-hip',core:'cat-core',stretch:'cat-stretch'}[ex.cat]||'cat-tone';
    const catLbl={cardio:'Cardio',tone:'Toning',hip:'Hip Care',core:'Core',stretch:'Flexibility'}[ex.cat]||'';
    const ov=document.getElementById('overlay');ov.classList.remove('hidden');
    ov.innerHTML='<div class="overlay-content ex-info"><h3>'+ex.name+'</h3><span class="cat-tag '+catCls+'">'+catLbl+'</span><a href="'+ex.yt+'" target="_blank" class="yt-link" style="margin-left:8px">\u25b6 Watch Demo</a>'+(ex.form?'<ol class="form-steps" style="margin-top:12px">'+ex.form.map(s=>'<li>'+s+'</li>').join('')+'</ol>':'')+'<button class="close-btn" id="close-ov">Got it</button></div>';
    document.getElementById('close-ov').addEventListener('click',()=>ov.classList.add('hidden'));
    ov.addEventListener('click',e=>{if(e.target===ov)ov.classList.add('hidden');});
  },

  // ---- DAY DETAIL ----
  showDay(dateStr){
    const parts=dateStr.split('-'),date=new Date(parseInt(parts[0]),parseInt(parts[1])-1,parseInt(parts[2]));
    const w=S.startDate?workoutFor(date):null;
    if(!w||w.type==='rest')return;
    const ov=document.getElementById('overlay');ov.classList.remove('hidden');
    let c='<div class="overlay-content"><h3 style="margin-bottom:4px">'+w.name+'</h3><div style="font-size:13px;color:var(--muted);margin-bottom:12px">'+w.focus+' \u00b7 '+w.dur+'</div>';
    w.exercises.forEach(ex=>{
      if(ex.section){c+='<div class="section-marker">'+ex.section+'</div>';return;}
      const info=EX[ex.id];if(!info)return;
      const rx=ex.duration||ex.hold||(ex.sets?ex.sets+'\u00d7'+ex.reps:ex.reps);
      c+='<div style="padding:6px 0;border-bottom:1px solid var(--border)"><div style="display:flex;justify-content:space-between"><span style="font-weight:600;font-size:13px">'+info.name+'</span><span style="color:var(--muted);font-size:12px">'+rx+'</span></div>'+(ex.protocol?'<div style="font-size:11px;color:var(--cardio)">'+ex.protocol+'</div>':'')+'</div>';
    });
    c+='<button class="close-btn" id="close-ov">Close</button></div>';
    ov.innerHTML=c;
    document.getElementById('close-ov').addEventListener('click',()=>ov.classList.add('hidden'));
    ov.addEventListener('click',e=>{if(e.target===ov)ov.classList.add('hidden');});
  },

  // ---- PLANS MENU ----
  showPlansMenu(){
    const ov=document.getElementById('overlay');ov.classList.remove('hidden');
    const plans=Plans.getAll(),hasData=!!S.startDate;
    const pi=hasData?phaseFor(norm(new Date())):null;
    let h='<div class="overlay-content"><h3 style="margin-bottom:16px">Plans</h3>';
    if(hasData){h+='<div class="section-title">Current</div><div style="font-size:13px;margin-bottom:12px">Started: '+fmt(norm(S.startDate))+'<br>'+(pi?pi.phase.name+' \u00b7 Week '+pi.wip:'Complete')+'</div>';}
    if(hasData){h+='<div class="section-title">Save Current</div><div style="display:flex;gap:8px;margin-bottom:16px"><input type="text" id="plan-name-in" placeholder="Plan name" style="flex:1;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--rs);color:var(--text);font-size:13px"><button id="save-plan-btn" style="padding:8px 16px;background:var(--primary);color:#150f1a;border:none;border-radius:var(--rs);font-size:13px;font-weight:700;cursor:pointer">Save</button></div>';}
    h+='<div class="section-title">Saved Plans</div>';
    if(plans.length){plans.forEach(p=>{const d=new Date(p.savedAt).toLocaleDateString('en',{month:'short',day:'numeric',year:'numeric'});h+='<div class="plan-item"><div class="plan-item-info"><div class="plan-item-name">'+p.name+'</div><div class="plan-item-date">'+d+'</div></div><div class="plan-item-btns"><button class="plan-btn-load" data-pn="'+p.name+'">Load</button><button class="plan-btn-del" data-pn="'+p.name+'">Del</button></div></div>';});}
    else{h+='<div style="font-size:13px;color:var(--dim);padding:8px 0">No saved plans yet.</div>';}
    h+='<div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)"><button id="new-plan-btn" style="width:100%;padding:10px;background:var(--card);border:1px solid var(--border);border-radius:var(--rs);color:var(--text);font-size:13px;font-weight:600;cursor:pointer">New Journey (Reset)</button></div>';
    h+='<button class="close-btn" id="close-ov">Close</button></div>';
    ov.innerHTML=h;
    const closeOv=()=>ov.classList.add('hidden');
    document.getElementById('close-ov').addEventListener('click',closeOv);
    ov.addEventListener('click',e=>{if(e.target===ov)closeOv();});
    const saveBtn=document.getElementById('save-plan-btn');
    if(saveBtn)saveBtn.addEventListener('click',()=>{const name=document.getElementById('plan-name-in').value.trim();if(!name)return;Plans.save(name);this.showPlansMenu();});
    document.querySelectorAll('.plan-btn-load').forEach(b=>b.addEventListener('click',()=>{if(confirm('Load "'+b.dataset.pn+'"? This replaces your current plan.')){Plans.load(b.dataset.pn);closeOv();this.render();}}));
    document.querySelectorAll('.plan-btn-del').forEach(b=>b.addEventListener('click',()=>{if(confirm('Delete "'+b.dataset.pn+'"?')){Plans.del(b.dataset.pn);this.showPlansMenu();}}));
    document.getElementById('new-plan-btn').addEventListener('click',()=>{if(!hasData||confirm('Start fresh? Saved plans are kept.')){Plans.reset();closeOv();this.render();}});
  }
};

// ---- INIT ----
document.addEventListener('DOMContentLoaded',()=>App.init());
