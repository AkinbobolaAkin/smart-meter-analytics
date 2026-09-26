%% smartmeter-report.cls
%% Look and feel for the Smart Meter term-project reports. Styling lives here only.
%%
%% Class options:
%%   final   turn every \placeholder{} into a compile error, so nothing unfinished ships
%%   (all other options are passed to article, e.g. 12pt)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{smartmeter-report}[2026/09/26 Smart Meter term-project report class]

\newif\ifsm@final
\DeclareOption{final}{\sm@finaltrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt,letterpaper]{article}

% ---------------------------------------------------------------- page & fonts
\RequirePackage[margin=1in,headheight=14pt]{geometry}
\RequirePackage{amsmath}
\RequirePackage[T1]{fontenc}
\RequirePackage{newtxtext,newtxmath}
\RequirePackage[scaled=0.92]{helvet}
\RequirePackage{microtype}
\RequirePackage[english]{babel}
\RequirePackage{csquotes}

% ---------------------------------------------------------------- colours
% Palette taken from the course brief: navy headings, blue subheadings, orange callouts.
\RequirePackage[table]{xcolor}
\definecolor{smnavy}{HTML}{1F3864}
\definecolor{smblue}{HTML}{4472C4}
\definecolor{smteal}{HTML}{17A2A2}
\definecolor{smorange}{HTML}{ED7D31}
\definecolor{smpale}{HTML}{E8EEF8}
\definecolor{smrow}{HTML}{F3F5F9}
\definecolor{smgray}{HTML}{595959}

% ---------------------------------------------------------------- packages
\RequirePackage{graphicx}
\graphicspath{{figures/}}
\RequirePackage{booktabs,tabularx,array,multirow}
\RequirePackage{siunitx}
\sisetup{group-separator={,}, group-minimum-digits=4}
\RequirePackage[shortlabels]{enumitem}
\setlist{itemsep=2pt, topsep=4pt}
\RequirePackage{float}
\RequirePackage{caption,subcaption}
\captionsetup{font=small, labelfont={bf,color=smnavy}, labelsep=period, skip=6pt}
\RequirePackage[most]{tcolorbox}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\RequirePackage{titlesec}
\RequirePackage[backend=biber, style=authoryear, maxcitenames=2, uniquelist=false,
  uniquename=false, dashed=false]{biblatex}
\addbibresource{references.bib}

% ---------------------------------------------------------------- headings
\titleformat{\section}
  {\sffamily\Large\bfseries\color{smnavy}}{\thesection}{0.6em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries\color{smblue}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\color{smnavy}}{\thesubsubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{16pt plus 4pt minus 2pt}{6pt plus 2pt}
\titlespacing*{\subsection}{0pt}{10pt plus 3pt minus 2pt}{4pt plus 2pt}
\setlength{\parskip}{4pt plus 1pt}
\setlength{\parindent}{0pt}

% ---------------------------------------------------------------- metadata
\newcommand{\sm@projecttitle}{Untitled project}
\newcommand{\sm@shorttitle}{\sm@projecttitle}
\newcommand{\sm@team}{}
\newcommand{\sm@course}{}
\newcommand{\sm@submission}{}
\newcommand{\sm@phase}{}
\newcommand{\sm@phasename}{}
\newcommand{\sm@deliverable}{}
\newcommand{\projecttitle}[1]{\renewcommand{\sm@projecttitle}{#1}}
\newcommand{\shorttitle}[1]{\renewcommand{\sm@shorttitle}{#1}}
\newcommand{\team}[1]{\renewcommand{\sm@team}{#1}}
\newcommand{\course}[1]{\renewcommand{\sm@course}{#1}}
\newcommand{\submissiondate}[1]{\renewcommand{\sm@submission}{#1}}
\newcommand{\phase}[1]{\renewcommand{\sm@phase}{#1}}
\newcommand{\phasename}[1]{\renewcommand{\sm@phasename}{#1}}
\newcommand{\deliverable}[1]{\renewcommand{\sm@deliverable}{#1}}

% ---------------------------------------------------------------- title block
\renewcommand{\maketitle}{%
  \thispagestyle{smfirst}%
  \begingroup
  \raggedleft{\sffamily\footnotesize\bfseries\color{smblue}
    TERM PROJECT \textbullet{} PHASE \sm@phase}\par
  \vspace{6pt}
  \raggedright
  {\sffamily\LARGE\bfseries\color{smnavy}\sm@projecttitle\par}
  \vspace{4pt}
  {\sffamily\Large\color{smblue}\sm@phasename\par}
  \vspace{4pt}
  {\color{smblue}\rule{\linewidth}{0.8pt}}\par
  \vspace{2pt}
  \small
  \ifx\sm@submission\@empty\else\textbf{Submission:} \sm@submission\quad|\quad\fi
  \textbf{Deliverable:} \sm@deliverable\par
  \ifx\sm@team\@empty\else\textbf{Team:} \sm@team\par\fi
  \ifx\sm@course\@empty\else\textbf{Course:} \sm@course\par\fi
  \endgroup
  \vspace{10pt}}

% ---------------------------------------------------------------- headers/footers
\fancypagestyle{smmain}{%
  \fancyhf{}%
  \fancyhead[L]{\sffamily\scriptsize\bfseries\color{smblue}TERM PROJECT \textbullet{} PHASE \sm@phase}%
  \fancyhead[R]{\sffamily\scriptsize\color{smgray}\sm@shorttitle}%
  \fancyfoot[C]{\sffamily\footnotesize\color{smgray}\thepage\ of \pageref*{LastPage}}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\headrule}{{\color{smblue!40}\hrule height\headrulewidth}}}
\fancypagestyle{smfirst}{%
  \fancyhf{}%
  \fancyfoot[C]{\sffamily\footnotesize\color{smgray}\thepage\ of \pageref*{LastPage}}%
  \renewcommand{\headrulewidth}{0pt}}
\pagestyle{smmain}

% ---------------------------------------------------------------- callout boxes
% Framed summary, e.g. a one-paragraph proposal overview.
\newtcolorbox{summarybox}[1][Summary]{enhanced, breakable, colback=smpale,
  colframe=smblue!70, boxrule=0.5pt, arc=0pt, left=6pt, right=6pt,
  fonttitle=\sffamily\bfseries\small, coltitle=white, colbacktitle=smnavy, title={#1}}
% Key point with a teal bar on the left.
\newtcolorbox{keyfinding}[1][Key finding]{enhanced, breakable, colback=white,
  colframe=white, borderline west={3pt}{0pt}{smteal}, boxrule=0pt, arc=0pt,
  left=8pt, top=2pt, bottom=2pt, fontupper=\small,
  before upper={\textbf{\color{smteal}#1:}\ }}

% ---------------------------------------------------------------- tables
% Navy header row:   \headrow \hd{Source} & \hd{Type} \\
% Striped body rows: put \smrows before \begin{tabular...}
\newcommand{\headrow}{\rowcolor{smnavy}}
\newcommand{\hd}[1]{\textcolor{white}{\sffamily\bfseries\small #1}}
\newcommand{\smrows}{\rowcolors{2}{smrow}{white}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}

% ---------------------------------------------------------------- inline helpers
\newcommand{\code}[1]{\texttt{\detokenize{#1}}}   % file, column and variable names
\newcommand{\kwh}{\si{\kilo\watt\hour}}
\newcommand{\kwhhh}{\si{\kilo\watt\hour} per half hour}
% Visible marker for unfinished text; a compile error under the `final` option.
\newcommand{\placeholder}[1]{%
  \ifsm@final
    \ClassError{smartmeter-report}{Unfinished placeholder: #1}{Remove the \string\placeholder\space before a final build.}%
  \else
    \ClassWarningNoLine{smartmeter-report}{Placeholder left in document}%
  \fi
  \textcolor{smorange}{\itshape[#1]}}

% ---------------------------------------------------------------- links (load last)
\RequirePackage[colorlinks=true, linkcolor=smnavy, citecolor=smblue, urlcolor=smblue]{hyperref}
\RequirePackage[capitalise, noabbrev]{cleveref}
\AtBeginDocument{\hypersetup{pdftitle={\sm@projecttitle{} -- Phase \sm@phase}}}
\endinput
