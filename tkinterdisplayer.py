import tkinter as tk                # python 3
from tkinter import font  as tkfont # python 3
#import Tkinter as tk     # python 2
#import tkFont as tkfont  # python 2
from lstm_model import generateFromLoaded2HipHop

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo,PageThree,PageFour):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Choisissez votre type musical", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        button1 = tk.Button(self, text="Hip Hop (intrument de base : piano)",
                            command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(self, text="Pop (instrument de base : piano)",
                            command=lambda: controller.show_frame("PageTwo"))

        button3 = tk.Button(self, text="Jazz (instrument de base : saxophone)",
                            command=lambda: controller.show_frame("PageThree"))

        button4 = tk.Button(self, text="Classical (instrument de base : saxophone)",
                            command=lambda: controller.show_frame("PageFour"))

        button1.pack()
        button2.pack()
        button3.pack()
        button4.pack()


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Hip Hop (avec instrument de base : Piano)", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        frame1 = tk.Frame(self, bg='white')
        frame1.pack(expand=True, fill=tk.BOTH)

        button = tk.Button(self, text="Générer",
                           command=lambda: self.hiphopGenerator(varDrums.get(),varBasse.get(),varGuitare.get()))
        buttonExit = tk.Button(self, text="<--",
                           command=lambda: controller.show_frame("StartPage"))

        varDrums = tk.IntVar()
        tk.Checkbutton(frame1, text='Percussion', variable=varDrums).grid(row=0, sticky=tk.W)
        varBasse = tk.IntVar()
        tk.Checkbutton(frame1, text='Basse', variable=varBasse).grid(row=1, sticky=tk.W)
        varGuitare = tk.IntVar()
        tk.Checkbutton(frame1, text='Guitare', variable=varGuitare).grid(row=2, sticky=tk.W)

        button.pack(side=tk.RIGHT)
        buttonExit.pack(side=tk.LEFT)
        # varDrums = tk.IntVar()
        # tk.Checkbutton(self, text='Percussion', variable=varDrums).grid(row=0, sticky=tk.W)
        # varBasse = tk.IntVar()
        # tk.Checkbutton(self, text='Basse', variable=varBasse).grid(row=1, sticky=tk.W)
        # varGuitare = tk.IntVar()
        # tk.Checkbutton(self, text='Guitare', variable=varGuitare).grid(row=2, sticky=tk.W)



    def hiphopGenerator(self,percussion=0,basse=0,guitare=0):
        print("percussion is " + str(percussion) + str(basse) + str(guitare))
        generateFromLoaded2HipHop("piano3hiphop.hdf5","Marvin_Gaye_-_I_Heard_It_Through_the_GrapevinePiano.mid","Piano",1,percussion=percussion,basse=basse,guitare=guitare)

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Pop (avec instrument de base : Piano)", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        frame1 = tk.Frame(self, bg='white')
        frame1.pack(expand=True, fill=tk.BOTH)

        button = tk.Button(self, text="Générer",
                           command=lambda: self.popGenerator(guitare=varGuitare.get(), violin=varViolon.get()))
        buttonExit = tk.Button(self, text="<--",
                               command=lambda: controller.show_frame("StartPage"))

        varGuitare = tk.IntVar()
        varViolon = tk.IntVar()
        tk.Checkbutton(frame1, text='Guitare', variable=varGuitare).grid(row=1, sticky=tk.W)
        tk.Checkbutton(frame1, text='Violon', variable=varViolon).grid(row=2, sticky=tk.W)

        button.pack(side=tk.RIGHT)
        buttonExit.pack(side=tk.LEFT)
        # varDrums = tk.IntVar()
        # tk.Checkbutton(self, text='Percussion', variable=varDrums).grid(row=0, sticky=tk.W)
        # varBasse = tk.IntVar()
        # tk.Checkbutton(self, text='Basse', variable=varBasse).grid(row=1, sticky=tk.W)
        # varGuitare = tk.IntVar()
        # tk.Checkbutton(self, text='Guitare', variable=varGuitare).grid(row=2, sticky=tk.W)



    def popGenerator(self,guitare=0,violin=0):
        #print("percussion is " + str(percussion) + str(basse) + str(guitare))
        generateFromLoaded2HipHop("piano3hiphop.hdf5","10_little_indians.mid","Piano",1,guitare=guitare,violon=violin,musicType=1)


class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Jazz (avec instrument de base : Saxophone)", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        frame1 = tk.Frame(self, bg='white')
        frame1.pack(expand=True, fill=tk.BOTH)

        button = tk.Button(self, text="Générer",
                           command=lambda: self.jazzGenerator())
        buttonExit = tk.Button(self, text="<--",
                               command=lambda: controller.show_frame("StartPage"))




        button.pack(side=tk.RIGHT)
        buttonExit.pack(side=tk.LEFT)
        # varDrums = tk.IntVar()
        # tk.Checkbutton(self, text='Percussion', variable=varDrums).grid(row=0, sticky=tk.W)
        # varBasse = tk.IntVar()
        # tk.Checkbutton(self, text='Basse', variable=varBasse).grid(row=1, sticky=tk.W)
        # varGuitare = tk.IntVar()
        # tk.Checkbutton(self, text='Guitare', variable=varGuitare).grid(row=2, sticky=tk.W)



    def jazzGenerator(self):
        #print("percussion is " + str(percussion) + str(basse) + str(guitare))
        generateFromLoaded2HipHop("saxo.hdf5","maple_leaf_rag .mid","Saxophone",1,musicType=2)

class PageFour(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Classic (avec instrument de base : Saxophone)", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        frame1 = tk.Frame(self, bg='white')
        frame1.pack(expand=True, fill=tk.BOTH)

        button = tk.Button(self, text="Générer",
                           command=lambda: self.classicGenerator())
        buttonExit = tk.Button(self, text="<--",
                               command=lambda: controller.show_frame("StartPage"))




        button.pack(side=tk.RIGHT)
        buttonExit.pack(side=tk.LEFT)
        # varDrums = tk.IntVar()
        # tk.Checkbutton(self, text='Percussion', variable=varDrums).grid(row=0, sticky=tk.W)
        # varBasse = tk.IntVar()
        # tk.Checkbutton(self, text='Basse', variable=varBasse).grid(row=1, sticky=tk.W)
        # varGuitare = tk.IntVar()
        # tk.Checkbutton(self, text='Guitare', variable=varGuitare).grid(row=2, sticky=tk.W)



    def classicGenerator(self):
        #print("percussion is " + str(percussion) + str(basse) + str(guitare))
        generateFromLoaded2HipHop("beethoven_ode_to_joy.hdf5","beethoven_ode_to_joy.mid","Piano",musicType=3)


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()