// transfers.js — THIS is the only file you edit to curate the tracker.
//
// To add a player: copy one { ... } block below, paste it at the top of the list,
// change the values, and make sure there's a comma after the closing } .
//
// Rules:
//   - status must be EXACTLY one of: "In Portal", "Committed", "Signed", "Withdrawn"
//   - leave newSchool as ""  until the player commits somewhere
//   - hometown is where the player is from, e.g. "Madrid, Spain" (leave "" if unknown)
//   - dateUpdated is NOT shown on the card anymore, but it still controls the order
//     (newest first), so keep setting it to the date you add or update someone
//   - give every player a unique id (just use the next number)

const TRANSFERS = [
  { id: "21", name: "Marek Nano", status: "Committed", previousSchool: "Eastern Kentucky", newSchool: "St. John's", hometown: "Slovakia", classYear: "Fr.", dateUpdated: "2026-05-27" },
  { id: "22", name: "Asier Ayllon Prado", status: "Committed", previousSchool: "UIndy", newSchool: "MTSU", hometown: "Getafe, Spain", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "23", name: "Nikola Puntarič", status: "Committed", previousSchool: "Northern Illinois", newSchool: "UIC", hometown: "Ljubljana, Slovenia", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "24", name: "Raffi Ymer", status: "Committed", previousSchool: "Elon", newSchool: "Kentucky", hometown: "Sweden", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "25", name: "Jakub Volesky", status: "Committed", previousSchool: "Northern Arizona", newSchool: "VCU", hometown: "Czech Republic", classYear: "", dateUpdated: "2026-05-27" },
  { id: "26", name: "Andrew Delgado", status: "Committed", previousSchool: "Wake Forest", newSchool: "Georgia", hometown: "Greensboro, North Carolina", classYear: "R-Fr.", dateUpdated: "2026-05-27" },
  { id: "27", name: "Oscar Baumgartner", status: "Committed", previousSchool: "UNCW", newSchool: "St. Joseph's", hometown: "Vevey, Switzerland", classYear: "", dateUpdated: "2026-05-27" },
  { id: "28", name: "Setti Germano", status: "Signed", previousSchool: "Midwestern State", newSchool: "DePaul", hometown: "Carazinho, Brazil", classYear: "", dateUpdated: "2026-05-27" },
  { id: "29", name: "Jewan Labuschagne", status: "In Portal", previousSchool: "Nicholls State", newSchool: "", hometown: "Pretoria, South Africa", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "30", name: "Benjamin Martin", status: "Committed", previousSchool: "Ole Miss", newSchool: "Memphis", hometown: "Nort-sur-Erdre, France", classYear: "", dateUpdated: "2026-05-27" },
  { id: "31", name: "Sasa Markovic", status: "Committed", previousSchool: "LSU", newSchool: "SMU", hometown: "Loznica, Serbia", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "32", name: "Itamar Tapiro", status: "Committed", previousSchool: "Delaware", newSchool: "Coastal Carolina", hometown: "", classYear: "", dateUpdated: "2026-05-27" },
  { id: "33", name: "Matthieu Coignet", status: "In Portal", previousSchool: "Texas A&M Corpus Christi", newSchool: "", hometown: "Clamart, France", classYear: "", dateUpdated: "2026-05-27" },
  { id: "15", name: "Oskar Grzegorzewski", status: "Committed", previousSchool: "UTSA", newSchool: "UC Santa Barbara", hometown: "Marki, Poland", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "16", name: "Dragos Nicolae Cazacu", status: "In Portal", previousSchool: "Tennessee", newSchool: "", hometown: "Romania", classYear: "Fr.", dateUpdated: "2026-05-27" },
  { id: "17", name: "Yannic Nittmann", status: "Committed", previousSchool: "Clemson", newSchool: "Memphis", hometown: "Cologne, Germany", classYear: "Fr.", dateUpdated: "2026-05-27" },
  { id: "18", name: "Caleb Saltz", status: "Committed", previousSchool: "Boston College", newSchool: "Miami (FL)", hometown: "Canyon Country, California", classYear: "Sr.", dateUpdated: "2026-05-27" },
  { id: "19", name: "Filip Apltauer", status: "Committed", previousSchool: "TCU", newSchool: "Florida State", hometown: "Prague, Czech Republic", classYear: "Sr.", dateUpdated: "2026-05-27" },
  { id: "20", name: "Santi Padilla Cote", status: "Committed", previousSchool: "Stetson", newSchool: "Tulane", hometown: "Plantation, Florida", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "13", name: "Thomas Nelson", status: "Committed", previousSchool: "Old Dominion", newSchool: "Michigan State", hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "14", name: "Ashton Adesoro", status: "Signed", previousSchool: "Western Michigan", newSchool: "Miami (FL)", hometown: "", classYear: "Sr.", dateUpdated: "2026-05-27" },
  { id: "12", name: "Hamza Nasridinov",    status: "Signed",  previousSchool: "Auburn",  newSchool: "Texas A&M",    hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "2",  name: "Alan Bojarski",     status: "Signed",  previousSchool: "Auburn", newSchool: "Tennessee",         hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "10", name: "Oscar Lacides",   status: "Committed",  previousSchool: "Oklahoma",  newSchool: "Tennessee",          hometown: "", classYear: "Sr.", dateUpdated: "2026-05-27" },
  { id: "1",  name: "Orel Kihmi",       status: "Committed",  previousSchool: "Oklahoma",   newSchool: "Tennessee",    hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "8",  name: "Hank Trondson",       status: "Committed",  previousSchool: "Oklahoma",  newSchool: "Oklahoma State",          hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "5",  name: "Jan Kobierski",    status: "Committed",  previousSchool: "Tennessee", newSchool: "San Diego State",   hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "9",  name: "Piotr Siekanowicz",     status: "Committed",  previousSchool: "Tennessee",  newSchool: "San Diego State", hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "3",  name: "Ariel Zauber",  status: "Committed",     previousSchool: "Wake Forest",     newSchool: "Indiana",       hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "7",  name: "Blake Anderson",     status: "Signed",     previousSchool: "Baylor",       newSchool: "San Diego State",  hometown: "", classYear: "So.", dateUpdated: "2026-05-27" },
  { id: "6",  name: "Mats Bredschneijder",     status: "Committed",  previousSchool: "VCU",    newSchool: "Hawaii",          hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "11", name: "Arsene Pougault",     status: "Signed",     previousSchool: "Arkansas, Charlotte",  newSchool: "Boise State",   hometown: "", classYear: "Jr.", dateUpdated: "2026-05-27" },
  { id: "4",  name: "Nicholas Heng",      status: "Signed",  previousSchool: "Auburn", newSchool: "Michigan",        hometown: "", classYear: "R-Sr.", dateUpdated: "2026-05-27" },
];
