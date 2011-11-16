<?php

// hmm, absolute path ??
//~ $skills_dir = "E:/code/TCPServer/PHPSkills/Skills/";
$skills_dir = "./PHPSkills/Skills/";

require_once($skills_dir.'TrueSkill/FactorGraphTrueSkillCalculator.php');
require_once($skills_dir.'GameInfo.php');
require_once($skills_dir.'Player.php');
require_once($skills_dir.'Rating.php');
require_once($skills_dir.'Team.php');
require_once($skills_dir.'Teams.php');
require_once($skills_dir.'SkillCalculator.php');

use Moserware\Skills\TrueSkill\FactorGraphTrueSkillCalculator;
use Moserware\Skills\GameInfo;
use Moserware\Skills\Player;
use Moserware\Skills\Rating;
use Moserware\Skills\Team;
use Moserware\Skills\Teams;
use Moserware\Skills\SkillCalculator;

//
// our input:
//  mu sig rank
//  .. (one line for each player)
//  empty line
//
// our output:
//  new_mu new_sig
//  .. (one line for each player)

    try {
        $calculator = new FactorGraphTrueSkillCalculator();
        $game_info = new GameInfo(50.0,       // mu
                                  50.0/3.0,   // sigma
                                  50.0/6.0,   // beta
                                  50.0/300.0, // tau
                                  0.05);      // draw prob
		$ratings = array();
        $players = array();
        $teams = array();
        $rankings = array();
		for($i=0; $i<10; $i++) {
			$line = fgets(STDIN);
			$line = rtrim($line);
			if ($line=="") {
				break;
			}
			$toks = split(" ", $line);
            $player_id = $i;
            $ratings[] = new Rating($toks[0], $toks[1]);
            $players[] = new Player($player_id + 1);
            $teams[] = new Team($players[$player_id], $ratings[$player_id]);
			$rankings[$i] = $toks[2];
		}
		
        $new_ratings = $calculator->calculateNewRatings($game_info, $teams, $rankings);
    } catch (Exception $e) {
    }
	
    for ($player_id = 0, $size = sizeof($rankings); $player_id < $size; ++$player_id) {
        $new_rating = $new_ratings->getRating($players[$player_id]);
		print $new_rating->getMean() . " " . $new_rating->getStandardDeviation() . "\n";
    }

?>
