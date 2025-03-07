# Bulletverse.io

![Bulletverse.io](https://i.imgur.com/vn4pYBH.png)

A multiplayer tank battle game built with Pygame where players upgrade their tanks, battle enemies, and compete against other players.

## 🎮 Game Overview

Bulletverse.io is a fast-paced tank shooter game where players control a customizable tank in a top-down arena. Fight against AI enemies, collect powerups, and level up your tank's abilities. The game features both singleplayer and multiplayer modes, allowing you to test your skills solo or battle against friends.

## ✨ Features

- **Multiple Game Modes**: Play solo or host/join multiplayer games
- **Upgrade System**: Level up and enhance your tank's abilities
- **Powerups**: Collect various powerups to gain temporary advantages
- **Particle Effects**: Attractive visual effects for an immersive experience
- **Tank Customization**: Choose from various tank colors
- **Difficulty Levels**: Select between Easy, Normal, and Hard difficulties
- **Discord Integration**: Shows your game status on Discord

## 🎯 Game Mechanics

- **Movement**: Use WASD keys to move your tank
- **Aiming**: Aim with your mouse
- **Shooting**: Left-click to fire
- **Upgrades**: Press U to open the upgrade menu
- **Menu**: Press ESC to return to the main menu

## 🔧 Installation

### Prerequisites
- Python 3.7+
- Pygame
- PyPresence (for Discord integration)
- NumPy

### Setup

1. Clone the repository:
```bash
git clone https://github.com/MadeBySosaCode/bulletverse.io.git
cd bulletverse.io
```

2. Install the required packages:
```bash
pip install pygame pypresence numpy
```

3. Run the game:
```bash
python play.py
```

### Running a Dedicated Server

You can run a dedicated server for multiplayer games:

```bash
python play.py --server
```

## 🔄 Game Controls

| Key/Action | Description |
|------------|-------------|
| W | Move up |
| A | Move left |
| S | Move down |
| D | Move right |
| Mouse | Aim |
| Left Click | Shoot |
| U | Open/Close Upgrade Menu |
| ESC | Return to Main Menu |
| M | Toggle Music |

## 🛠️ Upgrade System

As you defeat enemies and collect XP, you'll level up and earn upgrade points. These can be spent on:

- **Health Max**: Increases maximum health
- **Health Regen**: Adds passive health regeneration
- **Bullet Damage**: Increases damage per shot
- **Bullet Speed**: Makes bullets travel faster
- **Bullet Penetration**: Allows bullets to pass through multiple enemies
- **Reload Speed**: Reduces time between shots
- **Movement Speed**: Increases tank movement speed

## 🏆 Powerups

| Powerup | Effect |
|---------|--------|
| Health (Red) | Restores 25 health points |
| Shield (Blue) | Provides a temporary shield for 10 seconds |
| Speed (Green) | Increases movement speed for 5 seconds |
| Damage (Yellow) | Increases bullet damage for 8 seconds |
| XP (Purple) | Grants 30 experience points |

## 🎮 Game Modes

### Singleplayer
- Battle against AI enemies
- Three difficulty levels (Easy, Normal, Hard)
- Earn XP and upgrade your tank

### Multiplayer
- Host your own game server
- Join existing servers
- Compete against other players
- Collaborative gameplay

## 🖼️ Screenshots

*[Add your screenshots here]*

## 🔮 Future Plans

- Additional tank types with unique abilities
- New game modes (Capture the Flag, Team Deathmatch)
- Map editor
- Leaderboards
- More powerups and weapons
- Mobile version

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Pygame](https://www.pygame.org/) - The game framework used
- [PyPresence](https://github.com/qwertyquerty/pypresence) - For Discord integration
- [NumPy](https://numpy.org/) - For mathematical operations

---

Join our Discord server for updates and multiplayer coordination:
[Discord Server](https://discord.gg/XVN6mYv5AJ)
