# Golem_task

**Bus factor** is a measurement which attempts to estimate the number of key persons a project would need to lose in order for it to become stalled due to lack of expertise. It is commonly used in the context of software development.

**Input**: programming language name, number of projects to consider
**Output**: list of tuples containing the project's name, top contributor's name and their contribution percentage

Example:

```
python3 bus_factor.py --language rust --project_count 50

project: 996.ICU        user: 996icu         percentage: 0.80
project: ripgrep        user: BurntSushi     percentage: 0.89
project: swc            user: kdy1           percentage: 0.78
project: Rocket         user: SergioBenitez  percentage: 0.86
project: exa            user: ogham          percentage: 0.85
project: rustdesk       user: rustdesk       percentage: 0.80
project: appflowy       user: appflowy       percentage: 0.79
project: sonic          user: valeriansaliou percentage: 0.92
project: iced           user: hecrj          percentage: 0.89
project: delta          user: dandavison     percentage: 0.87
project: navi           user: denisidoro     percentage: 0.77
project: pyxel          user: kitao          percentage: 0.98
project: hyper          user: seanmonstar    percentage: 0.79
project: book           user: carols10cents  percentage: 0.76
project: xsv            user: BurntSushi     percentage: 0.92
```

----

The program processes pages and contributor's statistics for each project in parallel. Due to this, when the parameter ` project_count` is increased, the duration of the program almost does not grow and remains at the level of 15 seconds.
