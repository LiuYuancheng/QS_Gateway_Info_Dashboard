import wx
import wx.lib.agw.piectrl as PC


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelPieChart(wx.Panel):
    """ chart to display data based on time.
    """
    def __init__(self, parent, pnlSize=(320, 320)):
        wx.Panel.__init__(self, parent, size=pnlSize)
        self.SetBackgroundColour(wx.Colour(18, 86, 133))

    
        mSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mypie = PC.PieCtrl(self, -1, wx.DefaultPosition, wx.Size(180,270))
        self.mypie.SetBackColour(wx.Colour(150, 200, 255))
        
        self.part1 = PC.PiePart()
        self.part1.SetLabel("Average: 1")
        self.part1.SetValue(12)
        self.part1.SetColour(wx.Colour(0, 205, 52))
        self.mypie._series.append(self.part1)

        self.part2 = PC.PiePart()
        self.part2.SetLabel("Label 2")
        self.part2.SetValue(100-12)
        self.part2.SetColour(wx.Colour(83, 81, 251))
        self.mypie._series.append(self.part2)

        mSizer.Add(self.mypie, 1, wx.EXPAND | wx.ALL, 5)
        self.Layout()
        self.SetSizer(mSizer)
        #self.SetDoubleBuffered(True)

    def updatePieVals(self):
        a= random.randint(1,100)
        self.part1.SetValue(a)
        self.part1.SetLabel('data %s' %str(a))
        b = 100 -a 
        self.part1.SetValue(b)
        self.part1.SetLabel('data %s' %str(b))
        #self.Refresh(False)



class MyFrame(wx.Frame):

    def __init__(self, parent):

        wx.Frame.__init__(self, parent, -1, "PieCtrl Demo")

        panel = PanelPieChart(self)
        return
        panel.SetBackgroundColour(wx.Colour(18, 86, 133))
        # create a simple PieCtrl with 3 sectors
        mypie = PC.PieCtrl(panel, -1, wx.DefaultPosition, wx.Size(180,270))
        mypie.SetBackColour(wx.Colour(18, 86, 133))

        part1 = PC.PiePart()

        part1.SetLabel("Label 1")
        part1.SetValue(300)
        part1.SetColour(wx.Colour(200, 50, 50))
        mypie._series.append(part1)

        part2 = PC.PiePart()

        part2.SetLabel("Label 2")
        part2.SetValue(200)
        part2.SetColour(wx.Colour(50, 200, 50))
        mypie._series.append(part2)

        #part = PC.PiePart()

        #part.SetLabel("helloworld label 3")
        #part.SetValue(50)
        #part.SetColour(wx.Colour(50, 50, 200))
        #mypie._series.append(part)

        part1.SetValue(250)
        part2.SetValue(250)

        # create a ProgressPie
        progress_pie = PC.ProgressPie(panel, 100, 50, -1, wx.DefaultPosition,
                                      wx.Size(180, 200), wx.SIMPLE_BORDER)

        progress_pie.SetBackColour(wx.Colour(150, 200, 255))
        progress_pie.SetFilledColour(wx.Colour(255, 0, 0))
        progress_pie.SetUnfilledColour(wx.WHITE)
        progress_pie.SetHeight(20)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        main_sizer.Add(mypie, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(progress_pie, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)
        main_sizer.Layout()


# our normal wxApp-derived class, as usual

app = wx.App(0)

frame = MyFrame(None)
app.SetTopWindow(frame)
frame.Show()

app.MainLoop()