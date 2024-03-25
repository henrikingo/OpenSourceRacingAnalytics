OSRA.tsLaps.aggregate([
  {$match:{_id:ObjectID("65924089ea392724d76854d4")}},
  {$project:
  "c": [${selectlap:csv}],
  "c": {$literal:[${selectlap:csv}]}
  "cc": {$literal: ${selectsession:json} },
  "ccccc": ${selectsession:json},
  "ddd": [${selectsession:singlequote}]
   }},
   {$unwind:"$cc"}
,   {$unwind:"$c"}
])


OSRA.tsMetrics.aggregate([
   {$project:
      {foo:
         {$in: ["$labels.track",
                  [${track:singlequote}]
               ]
         }
      }
   },
   {$match:{foo:true}}
])
