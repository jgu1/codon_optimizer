drop table if exists AA_nucleo;
create table AA_nucleo (
  id integer primary key autoincrement,
  AA_sequence text not null,
  nucleo_sequence text not null
);

drop table if exists codon;
create table codon (
  Codon text not null,  
  ThreeLetter text not null,
  OneLetter text not null,
  FullName text not null 
);
.separator "\t"
.import ./codon.txt codon
